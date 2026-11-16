# Magic Words

This file explains the Toontown Realms Magic Word system and how to add Magic Words.

## What is a Magic Word?

In Toontown Online, Magic Words were developer commands used by the developers to test out the game
or to make toggling certain functionality easier. In Toontown Realms however, Magic Words have been introduced
to the normal gameplay to provide more ways to mess around.

## How can I find Magic Words?

Magic Words can be found in the Spellbook Page in the Shticker Book or in the file **MagicWordIndex.py**
in the **toontown.spellbook** module.

## How are Magic Words structured?

Magic Words are structured as classes in the **MagicWordIndex.py** file described above.

Some flags used for the logic behind Magic Words are defined in **MagicWordConfig.py**,
which is also in the **toontown.spellbook** module.

### Attributes

The following are some attributes for Magic Words:

* #### hidden
  * If **True**:
    * Does not show up on the Spellbook page
* #### administrative
  * If **True**:
    * Meant for moderation
    * Affects Toons who are locked down (i.e. caged)
    * Can be used on Legit Mode servers
* #### aliases
  * Alternative names
* #### desc
  * A short description that shows up on the Spellbook page
* #### advancedDesc
  * A more detailed description
  * Shows up on the Spellbook page when clicking the "More Info" button
* #### example
  * Example of how to use
  * If there are arguments, this value is used to describe the arguments
  * Shows up on the Spellbook page
* #### execLocation
  * Location the code runs:
    * **MagicWordConfig.EXEC_LOC_CLIENT** for client
    * **MagicWordConfig.EXEC_LOC_SERVER** for server
* #### cooldown
  * Prevent spam 
  * Cooldown time only applies to those below the **"MODERATOR"** access level
* #### access
  * Required access level to use the Magic Word
  * Default value: **"USER"**
* #### affectRange
  * Sets who can be targeted:
    * **MagicWordConfig.AFFECT_SELF** for invoker only
    * **MagicWordConfig.AFFECT_OTHER** for other Toons only
    * **MagicWordConfig.AFFECT_BOTH** for both invoker and other Toons
    * Default value is all of these
* #### anyTarget
  * If **True**, disregard access level when targeting others
* #### args
  * Additional arguments for the code
  * The syntax of arguments is as follows:
  > [("name", str, False, ''), ("scale", float, True)]
  > 
  > [(argName, argType, isRequired, defaultVal (only needed if isRequired is False))]

### handleWord Method
      
All Magic Word classes must also have a method defined called **handleWord**. The definition looks like this:

```python
def handleWord(self, invoker, avId, toon, *args):
  pass
```

The meaning of the arguments of this method are as follows:
* #### invoker
  * The Toon who used the Magic Word
* #### avId
  * The doId representing the Toon being targeted
* #### toon
  * The DistributedObject representing the Toon being targeted
* #### args
  * The Magic Word's arguments (if any have been defined)
  
To show a custom message upon executing the Magic Word, use `return 'The message'` in the **handleWord** method.
Otherwise, the Magic Word will show a random phrase from **MagicWordConfig.MAGIC_WORD_SUCCESS_PHRASES**.
  
### Development Only

Near the bottom of **MagicWordIndex.py** are some Magic Words that are defined under an
`if __debug__:` statement. **These Magic Words are meant for use in development only.**
If you want to add a Magic Word that will for use in development, put it here.
    
## How do I use Magic Words?

Magic Words can be used by typing them into the chat.

### Magic Word Activators

In the game settings you can select from several **Magic Word Activators**. These are
used to tell the game that you are typing a Magic Word instead of a regular chat message.

To use a Magic Word, type your **Magic Word Activator character** then the Word
itself into the chat.

### Targeting

The targeting for Magic Words is based on the number of **Magic Word Activator characters**
you typed into the chat.

To target yourself, type one **Activator character** before typing the Magic Word.

To target a specific Toon, click on them to open their Toon Panel then type two **Activator
characters** before typing the Magic Word.

#### Zone Targeting

To target every Toon in your zone, type **zone** after typing your **Activator character(s)**.

Example:

> ~zoneoboe

#### Server Targeting

To target every Toon in the server, type **server** after typing your **Activator character(s)**.

Example:

> ~serveroboe

#### Access Level Targeting

To target every Toon greater than or equal to an access level, type **rank** followed immediately by the
**access level number** after typing your **Activator character(s)**.

Example:

> ~rank100oboe

#### Excluding Yourself

When targeting using **zone**, **server**, or **rank**, you can use two **Activator characters**
to exclude yourself from being affected.

Using one or three **Activator characters** will include you in these scenarios.

### Magic Word JSON

In the **config** folder there is a file to customize some settings of Magic Words without having to go into
the code. This file is called **spellbook.json**.

Example:

```json
{
  "settings":
  {
    "cooldown-bypass": "MODERATOR"
  },
  "words":
    [
      {
        "name": "SetPos",
        "access": "USER",
        "cooldown": 0,
        "anyTarget": false
      },
      {
        "name": "GetPos",
        "access": "USER",
        "cooldown": 0,
        "anyTarget": false
      }
   ]
}
```

Last but not least, there is another file called **bot.json**. This can be used to call Magic Words remotely from
various bots such as Discord. The dictionary inside the file is treated as a queue, with keys being the Magic Words
themselves and values being the arguments.

Example:
```json
{
  "announce": "hello friends",
  "startholiday" : 128
}
```

In this example, **announce** would be executed before **startholiday**. Not all Magic Words are currently supported
via this method however. Below is a list of all Magic Words that work with the bot functionality:

> * announce
>   * aliases:
>     * broadcast
> * startholiday
>  * aliases:
>    * setholiday
>    * holiday
> * endholiday
> * snap
> * banid
> * kickid
> * update
> * maintenance

This functionality is considered experimental. As such, the definitions for these are not found in
**MagicWordIndex.py**. They are instead found in **ToontownOfflineMagicWordManagerAI.py**.