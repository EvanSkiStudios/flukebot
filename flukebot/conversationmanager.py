import os


# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))
memories_location = str(running_dir) + "/memories/"


# "a" - Append - will append to the end of the file
# "w" - Write - will overwrite any existing content


def convo_write_memories(username, conversation_data):
    f = open(memories_location + f"{username}.txt", "a")
    f.write(str(conversation_data))
    f.close()



# open and read the file after the appending:
# f = open(memories_location+"test.txt", "r")
# print(f.read())

