import sys

if __name__ == "__main__":
    keys = {
        "discord_api_key": sys.argv[1],
        "openai_api_key": sys.argv[2]
    } if len(sys.argv) == 3 else {}
        
    from joe import main
    main(keys)