<drac2>
# Meta constants
ALIAS_NAME = "ptw"
ALIAS_VERSION = "0.01"
NEWLINE_DELIM = "\n"
COIN_META = load_json(get_gvar("4fbb9498-05b5-4fab-a1e7-8166bf19e53c"))

# Coins Meta-info Properties
COIN_POUCH_NAME = "coin_pouch_name"

# Tuning Constants
CHECK_DC = 15
DAYS_PER_PAY_CUT = 8
STARTING_WAGE = 4
MAXIMUM_WAGE = 6
SUCCESSES_FOR_RAISE = 3
FAILURES_FOR_PAY_CUT = 3
SUCCESSES_FOR_BONUS = 5
BONUS_REWARD = 5
LIFESTYLES = load_json(get_gvar("e32a5f14-8707-4dbd-ac69-479afd70c1c1"))

# Argument Names
ARG_BONUS = "b"

# Cvar Names
CVAR_PTW = "ptw_details"
CVAR_LIFESTYLE = "lifestyle"

# Lifestyle Cvar Properties
LS_LAST_LIFESTYLE = "last_lifestyle"
LS_WORK_MODIFIER = "work_modifier"

# CC Names
# Ideally, the success/fail CCs should be renamed so it's clear
# that they belong to the PTW namespace.
CC_SUCCESSES = "successes"
CC_FAILURES = "fails"
CC_DTDS = "DTD"

# Fields are currently identical to correpsonding args,
# but it's probably worthwhile to define separately, in case
# we ever decide to change the argument names.
FIELD_EMPLOYER = "employer"
FIELD_LAST_ATTENDED = "last_attended"
FIELD_WAGE = "wage"
FIELD_CHECK = "check"
FIELD_BONUS = "bonus"
FIELD_ADV = "advantage"

HELP_TEXT = f'''\
-title "PTW Help" -desc "Let\'s get this bread!

TO USE:
First, make sure your custom counters have been set up! If you haven\'t already done so, execute `!RC`.
Second, perform initial setup using the `new` subcommand.
Finally, just run `!{ALIAS_NAME}`.

__Usage:__
If your PTW is already configured, just execute `!ptw`

Otherwise, use `!{ALIAS_NAME} new` to configure your work details;
or `!{ALIAS_NAME} settings` to go back and make changes.

`!{ALIAS_NAME} new <employer_name> <check_name>] [-{ARG_BONUS} <check_bonus>] [adv]`
`!{ALIAS_NAME} settings [-{ARG_BONUS} <check_bonus>] [adv]`"

-f "new|When running `!{ALIAS_NAME} new`, you should provide, at minimum, \
an `employer_name` and a `check_name`.
__Examples:__
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance`
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance adv`

If your job calls for a tool check, your check name should be the stat associated with the tool.
Proficiency and expertise bonuses will not be automatically added, in this case;
to add them, provide a `new_bonuses_value`. You can chain multiple bonuses, and optionally annotate them.

__Examples:__
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" charisma -{ARG_BONUS} 2[proficiency]`
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" charisma -{ARG_BONUS} 2[proficiency] -{ARG_BONUS} \\"3[some bonus]\\" -{ARG_BONUS} 4`"

-f "settings|When running `!{ALIAS_NAME} settings`, you can change bonuses and advantage settings.
__Examples:__
`!{ALIAS_NAME} reset`
(Removes all bonuses and clears advantage)

`!{ALIAS_NAME} settings -{ARG_BONUS} \\"2[proficiency]\\"`
(Replaces bonuses, then adds a +2 proficiency bonus)"

-f "Next Time|Just run `!{ALIAS_NAME}`. 

__Examples:__
`!{ALIAS_NAME}`"

-f "help|`!{ALIAS_NAME} ?` or `!{ALIAS_NAME} help`
Displays this help message!"
'''

args = &&&
parsed_args = argparse(args)

if args and args[0] in ["?", "help"]:
    return HELP_TEXT

out = [
    f'-thumb {image}',
    f'-color {color}',
    f'-footer "!{ALIAS_NAME} ?"'
]

desc_builder = []
errors = []
job_modifications = []

# Abort if no lifestyle
if not exists(CVAR_LIFESTYLE):
    # TODO: When details are solidified, update this help text.
    return f'''\
-title "{name} needs a lifestyle!" \
-desc "You need to run `!lifestyle` before you can perform part-time work.
See <channel_name> blahblahblah

Example: `!lifestyle some sample command`"\
'''

last_lifestyle_name = load_json(lifestyle)[LS_LAST_LIFESTYLE]
lifestyle_details = LIFESTYLES[last_lifestyle_name]

if args and args[0] in ["new"]:
    out.append(f'-title "{name} is becoming gainfully employed!"')
    job_details = {key: None for key in [
        FIELD_EMPLOYER,
        FIELD_LAST_ATTENDED,
        FIELD_WAGE,
        FIELD_CHECK,
        FIELD_BONUS,
        FIELD_ADV]}

    job_details[FIELD_EMPLOYER] = args[1]
    job_details[FIELD_CHECK] = args[2]

    # region Assign Employer
    new_employer = args[1]
    job_details[FIELD_EMPLOYER] = new_employer
    job_details[FIELD_WAGE] = STARTING_WAGE
    job_modifications.append(f'Employer set to {new_employer}')
    # endregion

    # region Assign Check
    new_check = args[2]

    if new_check:
        matches = [x for x in get_raw().skills.keys() if new_check.lower() in x.lower()]
        check = matches[0] if matches else None

        if check:
            job_details[FIELD_CHECK] = check
            job_modifications.append(f'Skill check set to {new_check}')
        else:
            errors.append(f'''\
-f "Error: Invalid Check|`{new_check}` is not a valid check`.
Try again with the name of a skill or ability.

Examples:
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance`
(sets check to performance; will automatically include proficiency/expertise)

`!{ALIAS_NAME} new \\"The Drunken Yeti\\" charisma -{ARG_BONUS} 2`
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" charisma -{ARG_BONUS} \\"2[proficiency]\\"`
(Use this if you are working with a tool check. Sets check to Charisma, \
with a flat additional bonus of 2; you would use this to represent, \
for example, a +2 proficiency bonus.)"\
''')
    # endregion

    # region Assign Manual Bonuses
    new_bonuses = parsed_args.get(ARG_BONUS)

    if new_bonuses:
        job_details[FIELD_BONUS] = [str(bonus) for bonus in new_bonuses]
        job_modifications += [f'Check bonus added: {bonus}' for bonus in job_details[FIELD_BONUS]]

    job_details[FIELD_ADV] = parsed_args.adv()
    if job_details[FIELD_ADV] > 0:
        job_modifications.append("Check bonus added: Advantage")
    # endregion

elif args and args[0] in ["settings"]:
    out.append(f'-title "{name} is making some job changes! Previous settings will be replaced."')
    if exists(CVAR_PTW):
        job_details = load_json(ptw_details)
    else:
        return f'''\
-title "{name} needs to configure their part-time work!" \
-desc "You need to use `!ptw new` before you can perform part-time work.
See `!{ALIAS_NAME} ?` or ask a thrall for help.

Example: `!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance`"\
'''

    if len(args) > 1 and args[1] in ["reset"]:
        job_details[FIELD_BONUS] = None
        job_details[FIELD_ADV] = 0
        job_modifications.append("Reset all bonuses and advantage settings.")
    else:
        # region Assign Manual Bonuses
        new_bonuses = parsed_args.get(ARG_BONUS)

        if new_bonuses:
            job_details[FIELD_BONUS] = [str(bonus) for bonus in new_bonuses]
            job_modifications += [f'Check bonus added: {bonus}' for bonus in job_details[FIELD_BONUS]]

        job_details[FIELD_ADV] = parsed_args.adv()
        if job_details[FIELD_ADV] > 0:
            job_modifications.append("Check bonus added: Advantage")
        # endregion

else:
    out.append(f'-title "{name} does part-time work!"')
    if exists(CVAR_PTW):
        job_details = load_json(ptw_details)
    else:
        return f'''\
-title "{name} needs to configure their part-time work!" \
-desc "You need to use `!ptw new` before you can perform part-time work.
See `!{ALIAS_NAME} ?` or ask a thrall for help.

Example:
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance`"\
'''

    if get_cc(CC_DTDS) == 0:
        errors.append(f'-f "Error: No DTDs|You have no downtime days left!"')

    desc_builder.append(f'**Lifestyle:** {last_lifestyle_name.title()}')

    employer = job_details[FIELD_EMPLOYER]
    if employer:
        desc_builder.append(f'**Employer:** {employer.title()}')
    else:
        errors.append(f'''\
-f "Error: No Employer|You must configure ptw using `!{ALIAS_NAME} new`.
Example:
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance`"\
''')

    # region Check attendance, deliver pay cuts
    last_attended_sec = job_details[FIELD_LAST_ATTENDED]
    current_time_sec = time()
    if last_attended_sec:
        delta_sec = int(current_time_sec - float(last_attended_sec))
        days_elapsed = delta_sec // (24 * 60 * 60)
        hours = delta_sec % (24 * 60 * 60) // 3600

        desc_builder.append(f'**Last Attended:** {days_elapsed} day(s) and {hours} hour(s) ago.')

        pay_cuts = days_elapsed // DAYS_PER_PAY_CUT

        if pay_cuts > 0 and job_details[FIELD_WAGE]:
            previous_wage = job_details[FIELD_WAGE]
            job_details[FIELD_WAGE] -= pay_cuts

            desc_builder.append(f'Because of nonattendance, your wages have dropped from {previous_wage} to {job_details[FIELD_WAGE]}.')
    else:
        out.append(f'-f "Last Attended|This is your first day on the job!"')
    # endregion

    job_details[FIELD_LAST_ATTENDED] = current_time_sec

    check_name = job_details.get(FIELD_CHECK)
    if check_name and not errors and job_details[FIELD_WAGE] and job_details[FIELD_WAGE] > 0:

        adv_dice = job_details[FIELD_ADV]
        desc_builder.append(f'**Base Wage:** {job_details[FIELD_WAGE]}GP')
        desc_builder.append(f'**Checking:** {check_name}{" with advantage" if adv_dice > 0 else ""}')

        bonuses = [get_raw().skills.get(check_name)]
        if job_details[FIELD_BONUS]:
            bonuses += job_details[FIELD_BONUS]

        bonuses.append(f'{str(lifestyle_details[LS_WORK_MODIFIER])}[lifestyle]')

        bonus_suffix = " + ".join([str(bonus) for bonus in bonuses])

        dice_expr = f'{"2d20kh1" if adv_dice > 0 else "d20"} + {bonus_suffix}'

        result = vroll(dice_expr)
        desc_builder.append(f'**Result:** {result}')

        # Modify CCs
        mod_cc(CC_DTDS, -1)

        earnings = job_details[FIELD_WAGE]

        if result.total >= CHECK_DC:
            mod_cc(CC_SUCCESSES, 1)
            desc_builder.append("You **passed** the check!")

            current_successes = get_cc(CC_SUCCESSES)
            if current_successes == SUCCESSES_FOR_RAISE and job_details[FIELD_WAGE] < MAXIMUM_WAGE:
                job_details[FIELD_WAGE] += 1
                desc_builder.append(f'''\
You succeeded {current_successes} times this week, \
and have received a raise of 1GP!\
    ''')
                job_modifications.append(f'Wage increased to {job_details[FIELD_WAGE]}GP')

            if current_successes == SUCCESSES_FOR_BONUS:
                earnings += BONUS_REWARD
                desc_builder.append(f'''\
You succeeded {current_successes} times this week, \
and earned a bonus of {BONUS_REWARD}GP!\
    ''')
        else:
            mod_cc(CC_FAILURES, 1)
            desc_builder.append("You **failed** the check!")

            current_failures = get_cc(CC_FAILURES)
            if current_failures == FAILURES_FOR_PAY_CUT:
                job_details[FIELD_WAGE] -= 1
                job_modifications.append(f'Wage decreased to {job_details[FIELD_WAGE]}GP')

                desc_builder.append(f'''\
You failed {current_failures} times this week, \
and have received a pay cut of 1GP.\
''')

        desc_builder.append("")
        desc_builder.append(f'You earned a total of **{earnings}GP!**')
        out.append(f'-f "Downtime Days (-1)|{cc_str(CC_DTDS)}"')

        # region Automated Payment; taken from gvar 6b81db5d-a6ee-4a4d-b922-1557eb5f5ee4
        bagsLoaded = load_json(get("bags", '[[""]]'))
        pouch=([x for x in bagsLoaded if x[0]==COIN_META[COIN_POUCH_NAME]]+[[]])[0]

        if pouch == []:
            return f"""-f "Error|Coin pouch missing, please run `!coins`" """

        # TODO: This can be expanded to take an object containing a delta
        # for each cointype, if necessary. But for now, quick and easy~
        operations = [("gp", earnings)]

        for coinType, amount in operations:
            amount = amount
            pouch[1].update({coinType:pouch[1]["gp"]+amount})

        set_cvar("bags",dump_json(bagsLoaded))
        # endregion

    elif not check_name:
        errors.append(f'''\
-f "Error: No Check|You must set your skill check using `!{ALIAS_NAME} new`.

See `!{ALIAS_NAME} ?"\
''')

# Check if they've been fired
if job_details[FIELD_WAGE] and job_details[FIELD_WAGE] <= 0:
    desc_builder.clear()
    out.append(f'''\
-f "Fired!|Because your wage has dropped to zero, you have been **fired.**
If you got a new job, you will need to rerun `!{ALIAS_NAME} new`.

Example:
`!{ALIAS_NAME} new \\"The Drunken Yeti\\" performance`"\
''')

# Combine output
out.append(f'-desc "{NEWLINE_DELIM.join(desc_builder)}"')

if job_modifications:
    out.append(f'-f "Job Modifications|{NEWLINE_DELIM.join(job_modifications)}"')

if errors:
    errors.append('-desc "There were some problems with the command; no changes have been made."')
    errors.append(f'-footer "!{ALIAS_NAME} ?"')
    return " ".join(errors)
else:
    set_cvar(CVAR_PTW, dump_json(job_details))
    return " ".join(out)
</drac2>
