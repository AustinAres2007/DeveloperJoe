# Hello Administrator.

This is a prompt on how to use {0}.
This is assuming you have the knowledge of what AI Models are, and you know the rules of hierarchy with discord roles. If you do not know one, I recommend doing research.

A small rundown of those two principles will be given in this tutorial.

## How to lock AI Models

You may use the `/lock` command to lock a AI Model. It requires two arguments— The model of AI you want to lock, and the role you permit to use the locked model. For example:

`/lock GPT-4 @VIP`

This will make it so only users with the VIP role and above can use the GPT-4 Model.
“And above” meaning that say you have a role that is higher on the role hierarchy. Like this:

@Administrator > @Moderators > @VIP > @everyone

So above VIP would be Moderators and Administrators. Below VIP would be @everyone, that means anyone who does not have @VIP or above cannot use the GPT-4 Model.

**IMPORTANT NOTE: If no roles are added to a specified AI models lock list, is will be permitted to be used by all users.**

## How to unlock AI Models

You may use the `/unlock` command to unlock a AI Model. It requires the same two arguments as `/lock`— The model of AI you want to unlock, and the role you want to remove from the specified AI models lock list.

The rules of hierarchy apply here. If you had @VIP and @Administrator on here, and you did:

`/unlock GPT-4 @VIP`

That means only users with @Administrator and above can now use the GPT-4 Model. Whereas before, users with @VIP and above could use GPT-4.

## View lock list for all models

You may use the `/locks` command to view all roles on the lock list for all models. This command takes 0 arguments and is very simple to use.

## A Note

ChatGPT is NOT the same as GPT-3 and GPT-4. ChatGPT uses the GPT-3 Engine, and is trained for mainly text capabilities.