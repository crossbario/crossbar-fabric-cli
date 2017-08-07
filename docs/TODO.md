# Checks

    cbsh login
    cbsh login --code 5V39-YG4Y-JKUK

    cbsh --profile oberstet login
    cbsh --profile oberstet login --code 5V39-YG4Y-JKUK


# CLI refreshing

When we asynchronously receive eg a WAMP event, we want to trigger a refresh / rerender of the CLI (eg for the bottom toolbar.)

The prompt toolkit has a method

    prompt_toolkit.interface.CommandLineInterface.invalidate()

for that.

The question is, how to we call it?

