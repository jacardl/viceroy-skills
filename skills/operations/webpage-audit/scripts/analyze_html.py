#!/usr/bin/env python3
"""
Ultimate Webpage HTML Analysis Tool for Complete Web Audit
Enhanced version with 15+ comprehensive auditing dimensions:

1. Heading structure (H1-H6) - hierarchy, nesting, duplicates
2. Semantic HTML elements - accessibility and structure
3. Schema/JSON-LD markup - deep structured data analysis
4. Metadata analysis - Open Graph, Twitter Card, basic meta
5. Link analysis - internal/external/generic/navigation
6. Text-to-code ratio & content balance
7. Accessibility (WCAG) checks
8. Performance indicators
9. SEO fundamentals
10. Mobile-friendliness signals
11. Security headers detection
12. Image optimization analysis
13. CSS/JS dependency analysis
14. Social media integration
15. Content quality signals
16. AMP detection
17. PWA features detection
"""

import sys
import json
import re
from html.parser import HTMLParser
from collections import Counter, defaultdict

class UltimateWebpageAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        # 1. Heading structure
        self.headings = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}
        self.heading_text = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}
        self.current_heading = None
        
        # 2. Semantic HTML
        self.semantic_elements = Counter()
        self.div_spam_count = 0
        self.span_count = 0
        
        # 3. Schema/JSON-LD
        self.json_ld_scripts = []
        self.current_json_ld = None
        self.microdata_types = []
        self.rdfa_types = []
        
        # 4. Metadata
        self.meta_tags = []
        self.open_graph = {}
        self.twitter_card = {}
        self.basic_meta = {}
        self.viewport_meta = None
        
        # 5. Links
        self.links = {
            'internal': 0, 
            'external': 0, 
            'generic': 0,  # # or empty
            'nofollow': 0,
            'noopener': 0
        }
        self.link_texts = []
        self.anchors_without_text = 0
        
        # 6. Content
        self.total_tags = 0
        self.text_content = []
        self.in_body = False
        self.in_script = False
        self.in_style = False
        
        # 7. Images
        self.images = {
            'total': 0,
            'missing_alt': 0,
            'empty_alt': 0,
            'lazy_loaded': 0,
            'with_width': 0,
            'with_height': 0,
            'with_srcset': 0,
            'with_sizes': 0
        }
        self.image_alts = []
        
        # 8. Accessibility (ARIA, WCAG)
        self.accessibility = {
            'aria_attributes': 0,
            'roles': 0,
            'lang_specified': False,
            'skip_link_found': False,
            'form_labels': 0,
            'forms_without_labels': 0
        }
        
        # 9. Forms
        self.forms = {
            'total': 0,
            'with_labels': 0,
            'without_labels': 0
        }
        
        # 10. Performance indicators
        self.performance = {
            'inline_css': 0,
            'inline_js': 0,
            'external_css': 0,
            'external_js': 0,
            'total_external_resources': 0
        }
        
        # 11. SEO fundamentals
        self.seo = {
            'has_title': False,
            'title_length': 0,
            'has_description': False,
            'description_length': 0,
            'has_canonical': False,
            'has_robots': False,
            'has_hreflang': False
        }
        
        # 12. Mobile
        self.mobile = {
            'has_viewport': False,
            'viewport_user_scalable': True,
            'viewport_width_device_width': False
        }
        
        # 13. Security
        self.security = {
            'has_http_equiv_csp': False,
            'has_x_ua_compatible': False,
            'external_resource_without_https': 0
        }
        
        # 14. PWA/Modern features
        self.features = {
            'has_manifest': False,
            'has_service_worker': False,
            'is_amp': False,
            'has_schema_org': False
        }
        
        # 15. Social
        self.social = {
            'og_complete': False,
            'twitter_complete': False,
            'social_links_found': 0
        }
    
    def handle_starttag(self, tag, attrs):
        self.total_tags += 1
        attrs_dict = dict(attrs)
        
        # Track current context
        if tag == 'body':
            self.in_body = True
        elif tag == 'script':
            self.in_script = True
            self._check_script(tag, attrs_dict)
        elif tag == 'style':
            self.in_style = True
        
        # Count basic elements
        if tag == 'div':
            self.div_spam_count += 1
        elif tag == 'span':
            self.span_count += 1
        
        # 1. Headings
        if tag in self.headings:
            self.current_heading = tag
            self.headings[tag].append(attrs_dict.get('id', ''))
        
        # 2. Semantic HTML elements
        semantic_tags = [
            'main', 'nav', 'section', 'article', 'header', 
            'footer', 'aside', 'figure', 'figcaption', 'details',
            'summary', 'mark', 'time', 'data'
        ]
        if tag in semantic_tags:
            self.semantic_elements[tag] += 1
        
        # 3. JSON-LD scripts
        if tag == 'script':
            if attrs_dict.get('type') == 'application/ld+json':
                self.current_json_ld = ''
                self.features['has_schema_org'] = True
        
        # 4. Meta tags
        if tag == 'meta':
            self._analyze_meta(attrs_dict)
        
        # 5. Links
        if tag == 'a':
            self._analyze_link(attrs_dict)
        
        # 6. Images
        if tag == 'img':
            self._analyze_image(attrs_dict)
        
        # 7. Forms
        if tag == 'form':
            self.forms['total'] += 1
        
        # 8. Labels
        if tag == 'label':
            self.accessibility['form_labels'] += 1
        
        # 9. Check for ARIA attributes
        for attr in attrs_dict:
            if attr.startswith('aria-'):
                self.accessibility['aria_attributes'] += 1
            if attr == 'role':
                self.accessibility['roles'] += 1
        
        # 10. Check microdata
        if 'itemtype' in attrs_dict:
            self.microdata_types.append(attrs_dict['itemtype'])
            self.features['has_schema_org'] = True
        
        # 11. Check RDFa
        if 'typeof' in attrs_dict:
            self.rdfa_types.append(attrs_dict['typeof'])
        
        # 12. Check for external resources
        if tag in ['link', 'script']:
            href = attrs_dict.get('href') or attrs_dict.get('src', '')
            if href:
                self.performance['total_external_resources'] += 1
                if tag == 'link' and attrs_dict.get('rel') == 'stylesheet':
                    self.performance['external_css'] += 1
                if tag == 'script' and 'src' in attrs_dict:
                    self.performance['external_js'] += 1
                if href.startswith('http') and not href.startswith('https://'):
                    self.security['external_resource_without_https'] += 1
                if tag == 'link' and attrs_dict.get('rel') == 'manifest':
                    self.features['has_manifest'] = True
        
        # 13. AMP detection
        if tag == 'html' and 'amp' in attrs_dict:
            self.features['is_amp'] = True
    
    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
        elif tag == 'script':
            if self.current_json_ld is not None and self.current_json_ld.strip():
                self.json_ld_scripts.append(self.current_json_ld)
                self.current_json_ld = None
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
        
        self.current_heading = None
    
    def handle_data(self, data):
        # Collect heading text
        if self.current_heading:
            text = data.strip()
            if text:
                self.heading_text[self.current_heading].append(text)
        
        # Collect text content only in body, not in scripts/styles
        if self.in_body and not self.in_script and not self.in_style:
            text = data.strip()
            if text:
                self.text_content.append(text)
        
        # Collect JSON-LD content
        if self.current_json_ld is not None:
            self.current_json_ld += data
    
    def _analyze_meta(self, attrs):
        property = attrs.get('property', '')
        name = attrs.get('name', '')
        content = attrs.get('content', '')
        charset = attrs.get('charset', '')
        
        if charset:
            self.basic_meta['charset'] = charset
        
        if property:
            if property.startswith('og:'):
                self.open_graph[property] = content
            self.meta_tags.append(('property', property, content))
        elif name:
            if name.startswith('twitter:'):
                self.twitter_card[name] = content
            elif name == 'viewport':
                self.viewport_meta = content
                self.mobile['has_viewport'] = True
                self.mobile['viewport_width_device_width'] = 'device-width' in content
                if 'user-scalable=no' in content or 'maximum-scale=1' in content:
                    self.mobile['viewport_user_scalable'] = False
            elif name == 'title':
                self.seo['has_title'] = True
                self.seo['title_length'] = len(content) if content else 0
            elif name == 'description':
                self.seo['has_description'] = True
                self.seo['description_length'] = len(content) if content else 0
            elif name == 'robots':
                self.seo['has_robots'] = content
            elif name == 'hreflang':
                self.seo['has_hreflang'] = True
            elif name == 'generator':
                self.basic_meta['generator'] = content
            self.meta_tags.append(('name', name, content))
        
        # Check for http-equiv security headers
        http_equiv = attrs.get('http-equiv', '')
        if http_equiv:
            if http_equiv.lower() == 'content-security-policy':
                self.security['has_http_equiv_csp'] = True
            if http_equiv.lower() == 'x-ua-compatible':
                self.security['has_x_ua_compatible'] = True
        
        # Check canonical
        if property == 'canonical' or (attrs.get('rel') == 'canonical'):
            self.seo['has_canonical'] = True
    
    def _analyze_link(self, attrs):
        href = attrs.get('href', '')
        rel = attrs.get('rel', '')
        
        # Check for skip links
        if href == '#main' or href == '#content' or (attrs.get('id') and 'skip' in attrs.get('id').lower()):
            self.accessibility['skip_link_found'] = True
        
        # Check rel attributes
        if rel and 'nofollow' in rel:
            self.links['nofollow'] += 1
        if rel and 'noopener' in rel or 'noreferrer' in rel:
            self.links['noopener'] += 1
        
        # Categorize link
        if not href or href == '#' or href.strip() == '':
            self.links['generic'] += 1
        elif href.startswith('http'):
            self.links['external'] += 1
            # Check for social media links
            if any(domain in href.lower() for domain in ['facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'tiktok.com']):
                self.social['social_links_found'] += 1
        elif href.startswith('mailto:') or href.startswith('tel:'):
            self.links['generic'] += 1
        else:
            self.links['internal'] += 1
    
    def _analyze_image(self, attrs):
        self.images['total'] += 1
        
        if 'alt' not in attrs:
            self.images['missing_alt'] += 1
        elif attrs['alt'].strip() == '':
            self.images['empty_alt'] += 1
        else:
            self.image_alts.append(attrs['alt'])
        
        if 'loading' in attrs and attrs['loading'] == 'lazy':
            self.images['lazy_loaded'] += 1
        
        if 'width' in attrs:
            self.images['with_width'] += 1
        if 'height' in attrs:
            self.images['with_height'] += 1
        if 'srcset' in attrs:
            self.images['with_srcset'] += 1
        if 'sizes' in attrs:
            self.images['with_sizes'] += 1
    
    def _check_script(self, tag, attrs):
        if not attrs.get('src'):
            self.performance['inline_js'] += 1
        if attrs.get('type') == 'application/ld+json':
            pass  # already counted
    
    def _analyze_heading_hierarchy(self):
        """Analyze heading hierarchy for proper nesting and skipping"""
        levels = []
        counts = []
        for i, level in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            count = len(self.headings[level])
            counts.append(count)
            if count > 0:
                levels.append(i + 1)
        
        issues = []
        # Check for skipped levels
        if not levels:
            issues.append('no_headings')
        else:
            min_level = min(levels)
            expected = min_level
            for level in sorted(levels):
                if level > expected + 1:
                    issues.append(f'skipped_level_{expected+1}_to_{level}')
                expected = level
        
        # Check for multiple H1
        h1_count = len(self.headings['h1'])
        if h1_count > 1:
            issues.append(f'multiple_h1_{h1_count}')
        elif h1_count == 0:
            issues.append('no_h1')
        
        # Check duplicates
        duplicates = {}
        for level in self.heading_text:
            text_list = [t.lower().strip() for t in self.heading_text[level]]
            counter = Counter(text_list)
            dupes = [(text, count) for text, count in counter.items() if count > 1]
            if dupes:
                duplicates[level] = dupes
        
        return {
            'counts': {
                'h1': len(self.headings['h1']),
                'h2': len(self.headings['h2']),
                'h3': len(self.headings['h3']),
                'h4': len(self.headings['h4']),
                'h5': len(self.headings['h5']),
                'h6': len(self.headings['h6']),
            },
            'total': sum(len(v) for v in self.headings.values()),
            'issues': issues,
            'duplicates': duplicates,
            'has_proper_hierarchy': len(issues) == 0
        }
    
    def _analyze_schema(self):
        """Deep analyze schema markup"""
        schemas_found = []
        all_types = []
        parse_errors = 0
        
        # Parse JSON-LD
        for script in self.json_ld_scripts:
            try:
                data = json.loads(script)
                if isinstance(data, list):
                    for item in data:
                        if '@type' in item:
                            all_types.append(item['@type'])
                            schemas_found.append({
                                'type': item['@type'],
                                'format': 'json-ld',
                                'properties': list(item.keys())
                            })
                elif isinstance(data, dict):
                    if '@type' in data:
                        all_types.append(data['@type'])
                        schemas_found.append({
                            'type': data['@type'],
                            'format': 'json-ld',
                            'properties': list(data.keys())
                        })
            except json.JSONDecodeError:
                parse_errors += 1
        
        # Add microdata
        for itemtype in self.microdata_types:
            schema_type = itemtype.split('/')[-1]
            all_types.append(schema_type)
            schemas_found.append({
                'type': schema_type,
                'format': 'microdata',
                'properties': []
            })
        
        # Add RDFa
        for typeof in self.rdfa_types:
            parts = typeof.split()
            for t in parts:
                schema_type = t.split('/')[-1]
                all_types.append(schema_type)
                schemas_found.append({
                    'type': schema_type,
                    'format': 'rdfa',
                    'properties': []
                })
        
        return {
            'total_schemas': len(schemas_found),
            'schema_types': list(set(all_types)),
            'schemas_found': schemas_found,
            'parse_errors': parse_errors,
            'has_schemas': len(schemas_found) > 0,
            'json_ld_count': len(self.json_ld_scripts),
            'microdata_count': len(self.microdata_types),
            'rdfa_count': len(self.rdfa_types)
        }
    
    def _calculate_text_ratio(self):
        """Calculate text-to-HTML ratio"""
        total_text = sum(len(t) for t in self.text_content)
        # More accurate estimation: average tag length is longer with attributes
        estimated_code_length = self.total_tags * 35 + total_text
        text_ratio = (total_text / estimated_code_length * 100) if estimated_code_length > 0 else 0
        
        word_count = len(' '.join(self.text_content).split())
        
        return {
            'text_to_code_ratio': round(text_ratio, 1),
            'total_text_characters': total_text,
            'estimated_word_count': word_count,
            'total_html_tags': self.total_tags
        }
    
    def _analyze_metadata_completeness(self):
        """Check completeness of metadata"""
        required_og = ['og:title', 'og:description', 'og:image', 'og:url']
        found_og = [key for key in required_og if key in self.open_graph]
        og_complete = len(found_og) == len(required_og)
        
        required_twitter = ['twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
        found_twitter = [key for key in required_twitter if key in self.twitter_card]
        twitter_complete = len(found_twitter) >= 3  # At least 3 of 4
        
        self.social['og_complete'] = og_complete
        self.social['twitter_complete'] = twitter_complete
        
        return {
            'open_graph_count': len(self.open_graph),
            'twitter_card_count': len(self.twitter_card),
            'open_graph_complete': og_complete,
            'twitter_card_complete': twitter_complete,
            'missing_required_og': [k for k in required_og if k not in self.open_graph],
            'missing_required_twitter': [k for k in required_twitter if k not in self.twitter_card]
        }
    
    def _calculate_semantic_score(self):
        """Calculate semantic HTML usage score"""
        semantic_total = sum(self.semantic_elements.values())
        total_elements = self.total_tags
        semantic_ratio = (semantic_total / total_elements * 100) if total_elements > 0 else 0
        
        expected_semantic = ['main', 'nav', 'header', 'footer']
        found_expected = [tag for tag in expected_semantic if self.semantic_elements.get(tag, 0) > 0]
        missing_expected = [tag for tag in expected_semantic if self.semantic_elements.get(tag, 0) == 0]
        
        return {
            'semantic_elements_found': dict(self.semantic_elements),
            'total_semantic_elements': semantic_total,
            'semantic_ratio_percent': round(semantic_ratio, 2),
            'missing_core_semantic': missing_expected,
            'core_semantic_coverage': len(found_expected) / len(expected_semantic) * 100
        }
    
    def _analyze_accessibility(self):
        """Compile accessibility analysis"""
        score_factors = []
        issues = []
        
        if self.accessibility['lang_specified']:
            score_factors.append(10)
        else:
            issues.append('missing_language_attribute')
        
        if self.images['missing_alt'] == 0:
            score_factors.append(20)
        else:
            issues.append(f'{self.images["missing_alt"]}_images_missing_alt')
        
        if self.accessibility['skip_link_found']:
            score_factors.append(10)
        else:
            issues.append('no_skip_link')
        
        if self.accessibility['aria_attributes'] > 0:
            score_factors.append(10)
        
        return {
            'issues': issues,
            'aria_attributes_found': self.accessibility['aria_attributes'],
            'roles_found': self.accessibility['roles'],
            'images_missing_alt': self.images['missing_alt'],
            'skip_link_present': self.accessibility['skip_link_found'],
            'language_specified': self.accessibility['lang_specified'],
            'form_labels': self.accessibility['form_labels'],
            'total_forms': self.forms['total']
        }
    
    def get_complete_analysis(self):
        """Get all analysis results compiled"""
        # Run all analyzers
        heading_analysis = self._analyze_heading_hierarchy()
        schema_analysis = self._analyze_schema()
        text_analysis = self._calculate_text_ratio()
        metadata_analysis = self._analyze_metadata_completeness()
        semantic_analysis = self._calculate_semantic_score()
        accessibility_analysis = self._analyze_accessibility()
        
        # Calculate overall scores
        # 1. Heading score
        heading_score = 100
        heading_penalties = {
            'no_headings': -50,
            'no_h1': -30,
            'multiple_h1_2': -10,
            'multiple_h1': -20,
            'skipped_level': -15
        }
        for issue in heading_analysis['issues']:
            if issue.startswith('skipped'):
                heading_score -= 15
            elif issue == 'no_h1':
                heading_score -= 30
            elif issue == 'no_headings':
                heading_score -= 50
            elif issue.startswith('multiple_h1'):
                heading_score -= 20
        heading_score = max(0, heading_score)
        
        # 2. Schema score
        schema_score = 0
        if schema_analysis['has_schemas']:
            schema_score = 70 + (len(schema_analysis['schema_types']) * 5)
            if schema_analysis['parse_errors'] > 0:
                schema_score -= 10 * schema_analysis['parse_errors']
            if schema_analysis['json_ld_count'] > 0:
                schema_score += 10  # Prefer JSON-LD
            schema_score = min(100, schema_score)
        schema_score = max(0, schema_score)
        
        # 3. Semantic HTML score
        semantic_score = semantic_analysis['core_semantic_coverage']
        if semantic_analysis['total_semantic_elements'] > 10:
            semantic_score += 10
        elif semantic_analysis['total_semantic_elements'] == 0:
            semantic_score = 0
        semantic_score = min(100, max(0, semantic_score))
        
        # 4. Metadata score
        metadata_score = 0
        if self.seo['has_title']:
            metadata_score += 20
        if self.seo['has_description']:
            metadata_score += 20
        if metadata_analysis['open_graph_complete']:
            metadata_score += 25
        if metadata_analysis['twitter_card_complete']:
            metadata_score += 20
        if self.seo['has_canonical']:
            metadata_score += 10
        metadata_score = min(100, metadata_score)
        
        # 5. Content score
        content_score = 0
        ratio = text_analysis['text_to_code_ratio']
        if 25 <= ratio <= 40:
            content_score = 100
        elif 15 <= ratio < 25:
            content_score = 70 + (ratio - 15) * 3
        elif 40 < ratio <= 50:
            content_score = 70 + (50 - ratio) * 3
        elif ratio < 15:
            content_score = ratio * 4
        else:  # > 50
            content_score = (100 - ratio) * 2
        content_score = max(0, min(100, content_score))
        
        # 6. Accessibility score
        a11y_score = 100
        if self.images['missing_alt'] > 0:
            a11y_score -= min(40, self.images['missing_alt'] * 10)
        if not self.accessibility['lang_specified']:
            a11y_score -= 10
        if not self.accessibility['skip_link_found']:
            a11y_score -= 10
        if self.forms['total'] > 0 and self.accessibility['form_labels'] == 0:
            a11y_score -= 20
        a11y_score = max(0, a11y_score)
        
        # 7. Navigation/Link score
        total_links = sum(self.links.values())
        nav_score = 100
        if total_links == 0:
            nav_score = 0
        else:
            generic_ratio = self.links['generic'] / total_links
            nav_score -= generic_ratio * 100  # Penalize generic links
            if self.links['nofollow'] > 0:
                nav_score += 5  # Proper nofollow usage is good
            nav_score = max(0, nav_score)
        
        # 8. Mobile score
        mobile_score = 0
        if self.mobile['has_viewport']:
            mobile_score += 50
            if self.mobile['viewport_width_device_width']:
                mobile_score += 30
            if self.mobile['viewport_user_scalable']:
                mobile_score += 20
        mobile_score = max(0, mobile_score)
        
        # 9. Performance score
        perf_score = 100
        total_resources = self.performance['total_external_resources']
        if total_resources > 20:
            perf_score -= min(50, (total_resources - 20) * 2)
        perf_score = max(0, perf_score)
        
        # 10. Image optimization score
        image_score = 100
        if self.images['total'] > 0:
            missing_alt_ratio = self.images['missing_alt'] / self.images['total']
            image_score -= missing_alt_ratio * 40
            no_dimension_ratio = (self.images['total'] - self.images['with_width']) / self.images['total']
            image_score -= no_dimension_ratio * 20
            if self.images['lazy_loaded'] > 0:
                image_score += 10  # Good practice
            if self.images['with_srcset'] > 0:
                image_score += 10  # Good practice
        image_score = max(0, min(100, image_score))
        
        # 11. Security score
        security_score = 100
        if self.security.get('external_resource_without_https', 0) > 0:
            security_score -= 40
        if not self.security.get('has_http_equiv_csp', False):
            security_score -= 20
        security_score = max(0, security_score)

        # 12. Social media score
        social_score = 0
        if self.social.get('og_complete'):
            social_score += 50
        if self.social.get('twitter_complete'):
            social_score += 30
        if self.social.get('social_links_found', 0) > 0:
            social_score += 20
        social_score = min(100, social_score)

        # Overall AIO (AI Optimization) score — 12 dimensions, weights sum to 1.0
        aio_score = round(
            heading_score * 0.08 +
            schema_score * 0.12 +
            semantic_score * 0.08 +
            metadata_score * 0.12 +
            content_score * 0.12 +
            a11y_score * 0.10 +
            nav_score * 0.08 +
            mobile_score * 0.06 +
            perf_score * 0.06 +
            image_score * 0.06 +
            security_score * 0.06 +
            social_score * 0.06
        )
        
        return {
            # Overall
            'overall': {
                'ai_optimization_score': int(aio_score),
                'weighted_dimensions': 12
            },
            
            # Individual dimension scores
            'scores': {
                'heading_hierarchy': int(heading_score),
                'schema_markup': int(schema_score),
                'semantic_html': int(semantic_score),
                'metadata_seo': int(metadata_score),
                'content_balance': int(content_score),
                'accessibility': int(a11y_score),
                'navigation_links': int(nav_score),
                'mobile_friendly': int(mobile_score),
                'performance': int(perf_score),
                'image_optimization': int(image_score),
                'security': int(security_score),
                'social_media': int(social_score)
            },
            
            # Detailed analysis
            'heading_hierarchy': heading_analysis,
            'schema': schema_analysis,
            'text_content': text_analysis,
            'metadata': metadata_analysis,
            'semantic_html': semantic_analysis,
            'accessibility': accessibility_analysis,
            
            # Raw counts
            'links': self.links,
            'total_links': total_links,
            'images': self.images,
            'performance': self.performance,
            'seo_basics': self.seo,
            'mobile': self.mobile,
            'security': self.security,
            'features': self.features,
            'social': self.social,
            
            # Derived stats
            'div_to_semantic_ratio': round(self.div_spam_count / max(1, sum(self.semantic_elements.values())), 2),
            'total_words': text_analysis['estimated_word_count']
        }


def analyze_html(html_content):
    """Ultimate HTML analysis entry point"""
    # Check for html tag with lang attribute
    analyzer = UltimateWebpageAnalyzer()
    # Pre-check for language
    if '<html' in html_content.lower():
        match = re.search(r'<html[^>]+lang\s*=\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if match:
            analyzer.accessibility['lang_specified'] = True
    
    analyzer.feed(html_content)
    return analyzer.get_complete_analysis()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <html-file>")
        print("Or pipe HTML via stdin: cat page.html | python analyze_html.py")
        sys.exit(1)
    
    if sys.argv[1] == '-':
        html_content = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    
    analysis = analyze_html(html_content)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
