class ContentMatcher:
    def __init__(self, content_accs_for_parsing_list, content_accs_list):
        self.content_accs_for_parsing_list = content_accs_for_parsing_list
        self.content_accs_list = content_accs_list

    def match_unique_content(self):
        if len(self.content_accs_for_parsing_list) < len(self.content_accs_list):
            raise ValueError

        result = []

        unique_iterator = iter(self.content_accs_for_parsing_list)

        for acc in self.content_accs_list:
            unique_acc = next(unique_iterator)

            result.append([acc, unique_acc])

        return result


content_accs_for_parsing_list = ["parse1", "parse2", "parse3", "parse4", "parse5"]
content_accs_list = ["acc1", "acc2", "acc3"]

matcher = ContentMatcher(content_accs_for_parsing_list, content_accs_list)
matched_content = matcher.match_unique_content()

print(matched_content)
print(content_accs_for_parsing_list)
print(content_accs_list)
