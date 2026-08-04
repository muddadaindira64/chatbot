from app.memory.memory import (
    load_memory,
    save_memory
)

from app.memory.models import (
    ConversationMessage
)

from app.memory.extractor import (
    extract_user_memory
)



def get_memory_context():

    memory = load_memory()

    user = memory.user_memory


    return f"""
User Information:

Name: {user.name}
Role: {user.role}
Company: {user.company}

Skills:
{", ".join(user.skills)}

Projects:
{", ".join(user.projects)}
"""



def get_history():

    memory = load_memory()

    return [
        item.model_dump()
        for item in memory.history[-5:]
    ]



def add_conversation(
    role:str,
    content:str
):

    memory = load_memory()


    memory.history.append(
        ConversationMessage(
            role=role,
            content=content
        )
    )


    save_memory(memory)



def update_memory(
    message:str
):

    memory = load_memory()


    extracted = extract_user_memory(
        message
    )


    user = memory.user_memory


    if "name" in extracted:
        user.name = extracted["name"]


    if "role" in extracted:
        user.role = extracted["role"]


    if "skills" in extracted:

        for skill in extracted["skills"]:

            if skill not in user.skills:
                user.skills.append(skill)


    save_memory(memory)