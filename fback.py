#!/usr/bin/env python3

import argparse
import sys
import json
import re
import os
from urllib.parse import urlparse, urlunparse, urljoin
import tldextract
from typing import List, Dict, Set
import itertools

BANNER = '''                

     ____             _                _  _ _ _ _           
    | __ )  __ _  ___| | ___   _ _ __ | |/ (_) | | ___ _ __ 
    |  _ \\ / _` |/ __| |/ / | | | '_ \\| ' /| | | |/ _ \\ '__|
    | |_) | (_| | (__|   <| |_| | |_) | . \\| | | |  __/ |   
    |____/ \\__,_|\\___|_|\\_\\__,__| .__/|_|\\_\\_|_|_|\\___|_|   
                                |_|   
                                                            NoobHunter
'''

class FBack:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.patterns_path = os.path.join(self.script_dir, "patterns.json")
        self.extensions_path = os.path.join(self.script_dir, "extensions.json")
        
        self.backup_extensions = [
            "back", "backup", "bak", "bck", "bkup", "bckp", "bk", "backupdb", 
            "old", "swp", "tmp", "backup1", "bak2", "bak3", "bdb", "~", 
            "log", "save", "sav", "orig", "copy", "sh", "bash", "new"
        ]
        
        self.compress_extensions = [
            "zip", "rar", "tar.gz", "7z", "bz2", "tar", "gzip", "bzip", "bz"
        ]
        
        self.common_words = [
            "web", "fullbackup", "backup", "data", "site", "assets", 
            "logs", "web", "debug", "install"
        ]

        self.default_patterns = {
            "patterns": [
                "$domain_name.$ext",
                "$full_domain.$ext",
                "$subdomain.$domain_name.$ext",
                "$full_domain$num.$ext",
                "$domain_name$num.$ext",
                "$subdomain.$ext",
                "$file_name.$ext",
                "$file_name~",
                "$file_name.$num",
                "$file_name.$ext.$num",
                "$full_path.$ext",
                ".$file_name",
                ".$file_name.$num",
                ".$file_name.$ext.$num",
                ".$domain_name.$ext",
                ".$file_name.$ext",
                "$full_path~",
                "$path/.$file_name.$ext",
                "$word.$ext",
                "$path/$word.$ext",
                "$path/$word"
            ],
            "date-formats": [
                "$domain_name.%y.$ext",
                "$domain_name.%y-%m-%d.$ext",
                "$full_domain.%y-%m-%d.$ext",
                "$full_domain.%y%m%d.$ext",
                "$path/%y-%m-%d.$ext"
            ]
        }

    def extract_url_parts(self, url: str) -> Dict[str, str]:
        """Parse URL into components using tldextract for better domain parsing"""
        parsed_url = urlparse(url)
        full_domain = parsed_url.netloc
        subdomain = tldextract.extract(url).subdomain
        domain_name = tldextract.extract(url).domain
        tld = tldextract.extract(url).suffix
        path = parsed_url.path
        full_path = urlunparse(('', '', parsed_url.path, '', '', ''))
        file_name = path.split('/')[-1] if '.' in parsed_url.path.split('/')[-1] else ""

        return {
            "URL": url,
            "Full Domain": full_domain,
            "Subdomain": subdomain,
            "Domain Name": domain_name,
            "TLD": tld,
            "Path": path,
            "Full Path": full_path,
            "File Name": file_name,
        }

    def format_patterns(self, url: str, patterns: List[str]) -> List[str]:
        """Format patterns with URL components"""
        url_parts = self.extract_url_parts(url)
        formatted_patterns = []
        for pattern in patterns:
            formatted_pattern = pattern.replace("$domain_name", str(url_parts["Domain Name"]))
            formatted_pattern = formatted_pattern.replace("$full_domain", str(url_parts["Full Domain"]))
            formatted_pattern = formatted_pattern.replace("$subdomain", str(url_parts["Subdomain"]))
            formatted_pattern = formatted_pattern.replace("$tld", str(url_parts["TLD"]))
            formatted_pattern = formatted_pattern.replace("$file_name", str(url_parts["File Name"]))
            formatted_pattern = formatted_pattern.replace("$full_path", str(url_parts["Full Path"]))
            formatted_pattern = formatted_pattern.replace("$path", str(url_parts["Path"]))
            formatted_pattern = formatted_pattern.replace("..", ".").replace("//", "/")
            formatted_patterns.append(formatted_pattern)
        return formatted_patterns

    def generate_patterns_combinations(self, url: str, patterns: List[str], words: List[str], 
                                     extensions: List[str], numbers: List[str]) -> Set[str]:
        """Generate combinations of patterns with words, extensions and numbers"""
        results = set()
        for pattern in patterns:
            for word in words:
                for ext in extensions:
                    for num in numbers:
                        new_pattern = pattern.replace("$word", word).replace("$ext", ext).replace("$num", num)
                        if not self.contains_special_chars(new_pattern):
                            results.add(new_pattern)
        return results

    def generate_date_formats_combinations(self, url: str, date_formats: List[str], words: List[str], 
                                         extensions: List[str], numbers: List[str], 
                                         years: List[str], months: List[str], days: List[str]) -> Set[str]:
        """Generate combinations of date formats with words, extensions and numbers"""
        results = set()
        for date_format in date_formats:
            for word in words:
                for ext in extensions:
                    for num in numbers:
                        for year in years:
                            for month in months:
                                for day in days:
                                    new_date_format = date_format.replace("$word", word)
                                    new_date_format = new_date_format.replace("$ext", ext)
                                    new_date_format = new_date_format.replace("$num", num)
                                    new_date_format = new_date_format.replace("%y", year)
                                    new_date_format = new_date_format.replace("%m", month)
                                    new_date_format = new_date_format.replace("%d", day)
                                    if not self.contains_special_chars(new_date_format):
                                        results.add(new_date_format)
        return results

    def contains_special_chars(self, line: str) -> bool:
        """Check if line contains special characters"""
        return "$" in line or "%" in line

    def remove_components_until_path(self, urls: List[str]) -> List[str]:
        """Remove components from URLs until path"""
        nice_urls = []
        for url in urls:
            url = urljoin(url, urlparse(url).path)
            nice_urls.append(url)
        return list(set(nice_urls))

    def create_year_range(self, year_range: str) -> List[str]:
        """Create list of years from range string"""
        if '-' in year_range:
            start_year, end_year = map(int, year_range.split('-'))
            if len(str(start_year)) == 4 and len(str(end_year)) == 4:
                return [str(year) for year in range(start_year, end_year + 1)]
            else:
                raise ValueError("Invalid input format. Use 'YYYY-YYYY' or 'YYYY,YYYY'.")
        elif ',' in year_range:
            year_range = year_range.split(',')
            for year in year_range:
                if len(str(year)) != 4:
                    raise ValueError("Invalid input format. Use 'YYYY-YYYY' or 'YYYY,YYYY'.")
            return [str(year) for year in year_range]
        elif year_range.isdigit() and len(year_range) == 4:
            return [year_range]
        else:
            raise ValueError("Invalid input format. Use 'YYYY-YYYY' or 'YYYY,YYYY'.")

    def create_month_range(self, month_range: str) -> List[str]:
        """Create list of months from range string"""
        if '-' in month_range:
            start_month, end_month = map(int, month_range.split('-'))
            if 1 <= start_month <= 12 and 1 <= end_month <= 12:
                return [f"{month:02d}" for month in range(start_month, end_month + 1)]
            else:
                raise ValueError("Invalid input format. Use 'mm-mm' or 'mm,mm'.")
        elif ',' in month_range:
            month_range = month_range.split(',')
            for month in month_range:
                if not 1 <= int(month) <= 12:
                    raise ValueError("Invalid input format. Use 'mm-mm' or 'mm,mm'.")
            return [f"{int(month):02d}" for month in month_range]
        elif month_range.isdigit() and 1 <= int(month_range) <= 12:
            return [f"{int(month_range):02d}"]
        else:
            raise ValueError("Invalid input format. Use 'mm-mm' or 'mm,mm'.")

    def create_day_range(self, day_range: str) -> List[str]:
        """Create list of days from range string"""
        if '-' in day_range:
            start_day, end_day = map(int, day_range.split('-'))
            if 1 <= start_day <= 31 and 1 <= end_day <= 31:
                return [f"{day:02d}" for day in range(start_day, end_day + 1)]
            else:
                raise ValueError("Invalid input format. Use 'dd-dd' or 'dd,dd'.")
        elif ',' in day_range:
            day_range = day_range.split(',')
            for day in day_range:
                if not 1 <= int(day) <= 31:
                    raise ValueError("Invalid input format. Use 'dd-dd' or 'dd,dd'.")
            return [f"{int(day):02d}" for day in day_range]
        elif day_range.isdigit() and 1 <= int(day_range) <= 31:
            return [f"{int(day_range):02d}"]
        else:
            raise ValueError("Invalid input format. Use 'dd-dd' or 'dd,dd'.")

    def load_patterns(self, pattern_file=None):
        """Load patterns from a file or use default patterns."""
        if pattern_file and os.path.exists(pattern_file):
            try:
                with open(pattern_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in pattern file {pattern_file}")
                return self.default_patterns
            except Exception as e:
                print(f"Error loading pattern file: {e}")
                return self.default_patterns
        return self.default_patterns

def main():
    parser = argparse.ArgumentParser(
        description="Fback is a fast and dynamic tool to generate wordlist to find backup files.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Input options
    INPUT = parser.add_argument_group('Flags:\n INPUT')
    INPUT.add_argument('-p', '-pattern', dest='pattern_file', default=None, help='Pattern File Name (default "patterns.json")')
    INPUT.add_argument('-e', '-extensions', dest='extensions_file', default=None, help='Input file containing list of extensions with levels (default "extensions.json")')
    INPUT.add_argument('-o', '-output', dest='output_file', default=None, help='Name of the output file')
    
    # Output options
    OUTPUT = parser.add_argument_group(' OUTPUT')
    OUTPUT.add_argument('-wo', '-wordlistonly', action='store_true', dest='wordlist_only', help='Wordlist only')
    OUTPUT.add_argument('-jo', '-json-output', action='store_true', dest='json_output', help='Wordlist only in JSON format')
    
    # Levels Management
    LEVELS = parser.add_argument_group(' LEVELS MANAGEMENT')
    LEVELS.add_argument('-l', '-levels', dest='levels', default='1,2', help='Backup & Compress extensions level(s) [min:1 max:10] (default "1,2")')
    LEVELS.add_argument('-bl', '-backup-levels', dest='backup_levels', default=None, help='Backup extensions level(s) [min:1 max:10]')
    LEVELS.add_argument('-cl', '-compress-levels', dest='compress_levels', default=None, help='Compress extensions level(s) [min:1 max:10]')
    
    # Main methods
    MAIN_METHODS = parser.add_argument_group(' MAIN METHODS')
    MAIN_METHODS.add_argument('-w', '-wordlist', dest='wordlist', default=None, help='Wordlist method, to generate by words')
    
    # Date methods
    DATE_METHODS = parser.add_argument_group(' DATE METHODS')
    DATE_METHODS.add_argument('-dm', '-date-method', action='store_true', dest='date_method', help='Enable Date Method')
    DATE_METHODS.add_argument('-dc', '-date-custom', dest='date_custom', default=None, help='Custom Date format, e.g. \'$full_domain.%%y-%%m-%%d.$ext\' [separated by comma]')
    DATE_METHODS.add_argument('-dd', '-date-default', action='store_true', dest='date_default', help='Use default formats for date method in patterns.json')
    DATE_METHODS.add_argument('-yr', '-year-range', dest='year_range', default='2019-2022', help='Range of years (default "2019-2022")')
    DATE_METHODS.add_argument('-mr', '-month-range', dest='month_range', default='2,3', help='Range of months [min:1 max:12] (default "2,3")')
    DATE_METHODS.add_argument('-dr', '-day-range', dest='day_range', default='1-3', help='Range of days [min:1 max:31] (default "1-3")')
    
    # Other options
    OTHER = parser.add_argument_group(' OTHER OPTIONS')
    OTHER.add_argument('-nr', '-number-range', dest='number_range', default='1,2', help='Range of $num var in patterns (default "1,2")')
    OTHER.add_argument('-s', '-silent', action='store_true', dest='silent', help='Silent mode')
    
    args = parser.parse_args()
    
    try:
        fback = FBack()
        
        if not args.output_file and not args.silent:
            print(BANNER)

        if not sys.stdin.isatty():
            input_urls = [line.strip() for line in sys.stdin.readlines()]
            url_list = fback.remove_components_until_path(input_urls)
        else:
            print("Error: No input provided via stdin")
            sys.exit(1)

        # Load pattern file
        pattern_file = args.pattern_file if args.pattern_file else fback.patterns_path
        try:
            with open(pattern_file, 'r') as file:
                pattern_data = json.load(file)
        except FileNotFoundError:
            print(f"Error: Pattern file {pattern_file} not found")
            sys.exit(1)

        # Load extensions file
        extensions_file = args.extensions_file if args.extensions_file else fback.extensions_path
        try:
            with open(extensions_file, 'r') as file:
                extensions_data = json.load(file)
        except FileNotFoundError:
            print(f"Error: Extensions file {extensions_file} not found")
            sys.exit(1)

        # Load wordlist
        if not args.wordlist:
            print("Error: Wordlist file not provided")
            sys.exit(1)
        try:
            with open(args.wordlist, 'r') as file:
                words = [line.strip() for line in file]
        except FileNotFoundError:
            print(f"Error: Wordlist file {args.wordlist} not found")
            sys.exit(1)

        # Process extensions based on levels
        extensions = []
        if args.backup_levels:
            backup_levels = args.backup_levels.split(',')
            for level in backup_levels:
                if f"level{level}" in extensions_data.get("backup", {}):
                    extensions.extend(extensions_data["backup"][f"level{level}"])
        elif args.compress_levels:
            compress_levels = args.compress_levels.split(',')
            for level in compress_levels:
                if f"level{level}" in extensions_data.get("compress", {}):
                    extensions.extend(extensions_data["compress"][f"level{level}"])
        else:
            levels = args.levels.split(',')
            for level in levels:
                if f"level{level}" in extensions_data.get("backup", {}):
                    extensions.extend(extensions_data["backup"][f"level{level}"])
                if f"level{level}" in extensions_data.get("compress", {}):
                    extensions.extend(extensions_data["compress"][f"level{level}"])

        # Process number range
        if '-' in args.number_range:
            start_num, end_num = map(int, args.number_range.split('-'))
            number_range = [str(num) for num in range(start_num, end_num + 1)]
        else:
            number_range = args.number_range.split(',')

        # Process date ranges if date method is enabled
        year_range = month_range = day_range = None
        if args.date_method:
            year_range = fback.create_year_range(args.year_range)
            month_range = fback.create_month_range(args.month_range)
            day_range = fback.create_day_range(args.day_range)

        # Generate patterns
        final = {"patterns": set()}
        for url in url_list:
            formatted_patterns = fback.format_patterns(url, pattern_data.get("patterns", []))
            final["patterns"].update(fback.generate_patterns_combinations(url, formatted_patterns, words, extensions, number_range))

        # Generate date formats if enabled
        if args.date_method:
            final["date-formats"] = set()
            for url in url_list:
                if args.date_default:
                    date_formats = pattern_data.get("date-formats", [])
                elif args.date_custom:
                    date_formats = args.date_custom.split(",")
                else:
                    date_formats = []
                
                formatted_date_formats = fback.format_patterns(url, date_formats)
                final["date-formats"].update(fback.generate_date_formats_combinations(
                    url, formatted_date_formats, words, extensions, number_range,
                    year_range, month_range, day_range
                ))

        # Convert sets to lists for output
        final["patterns"] = list(final["patterns"])
        if "date-formats" in final:
            final["date-formats"] = list(final["date-formats"])

        # Generate output
        unique_output = set()
        if args.json_output:
            unique_output = final
            output = json.dumps(unique_output, indent=4)
        else:
            for url in url_list:
                for path in final["patterns"]:
                    if args.wordlist_only:
                        if path.startswith('/'):
                            path = path[1:]
                        unique_output.add(path)
                    else:
                        unique_output.add(urljoin(url, path))
                
                if args.date_method and "date-formats" in final:
                    for path in final["date-formats"]:
                        if args.wordlist_only:
                            if path.startswith('/'):
                                path = path[1:]
                            unique_output.add(path)
                        else:
                            unique_output.add(urljoin(url, path))
            
            output = '\n'.join(sorted(unique_output))

        # Write output
        if args.output_file:
            with open(args.output_file, 'w') as outfile:
                outfile.write(output)
        else:
            print(output)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 
