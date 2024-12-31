from src.list_builder import CharacterListBuilder, CountryListBuilder, OathListBuilder
import pyperclip


def main():
    builders = [CharacterListBuilder, CountryListBuilder, OathListBuilder]
    for i, builder in enumerate(builders, 1):
        print(f"{i}. {builder.__name__}")

    choice = int(input("\nSelect a list to generate: "))
    builder = builders[choice - 1]()
    wiki_table = builder.build()
    try:
        pyperclip.copy(wiki_table)
        print("\nTable copied to clipboard!")
    except Exception as e:
        print("\nFailed to copy to clipboard. Make sure pyperclip is installed:")
        print("pip install pyperclip")


if __name__ == "__main__":
    main()
