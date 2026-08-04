from app.memory.models import UserMemory


def extract_user_memory(
    message: str
) -> dict:

    extracted = {}


    text = message.lower()


    if "my name is" in text:

        name = (
            message
            .split("my name is")[-1]
            .strip()
        )

        extracted["name"] = name



    if "i am a" in text:

        role = (
            message
            .split("i am a")[-1]
            .strip()
        )

        extracted["role"] = role



    if "i know" in text:

        skills = (
            message
            .split("i know")[-1]
            .split(",")
        )

        extracted["skills"] = [
            x.strip()
            for x in skills
        ]


    return extracted