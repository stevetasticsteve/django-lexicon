# Functions that handle subprocess calls to hunspell

import subprocess
import tempfile


def unmunch(dic_content, aff_content):
    dic_content = check_length_dic_contents(dic_content)
    print(dic_content)

    # Create temporary files for the .dic and .aff data
    with (
        tempfile.NamedTemporaryFile(mode="w+", delete=True) as dic_temp,
        tempfile.NamedTemporaryFile(mode="w+", delete=True) as aff_temp,
    ):

        # Write the contents to the temp files
        dic_temp.write(dic_content)
        aff_temp.write(aff_content)

        # Ensure the data is flushed to disk
        dic_temp.flush()
        aff_temp.flush()

        # Call the unmunch command using the temporary files
        result = (
            subprocess.run(
                ["unmunch", dic_temp.name, aff_temp.name], stdout=subprocess.PIPE
            )
            .stdout.decode("utf-8")
            .strip()
        )
    return result


def check_length_dic_contents(dic_content: str) -> str:
    """Check if the provided dic words start with a number representing length.

    Returns a string with an updated length."""

    lines = dic_content.split("\n")

    if not lines[0].isdigit():
        lines.insert(0, str(100))

    return "\n".join(lines)
