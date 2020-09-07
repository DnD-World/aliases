<drac2>
# Meta constants
ALIAS_NAME = "ptw"
ALIAS_VERSION = "0.01"
NEWLINE_DELIM = "\n"

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

# Args
ARG_EMPLOYER = "e"
ARG_CHECK = "c"
ARG_BONUS = "b"

# Cvars
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

HELP_TEXT = f'''\
-title "PTW Help" -desc "Let\'s get this bread!

TO USE:
First, make sure your custom counters have been set up! If you haven\'t already done so, execute `!RC`.

__Syntax:__
`!{ALIAS_NAME} [-{ARG_EMPLOYER} <new_employer_name> -{ARG_CHECK} <new_check_name> -{ARG_BONUS} <check_bonus>] <adv>`"

-f "Initial Setup|The first time you run this command, you should provide, at minimum, a `new_employer_name` and a `new_check_name`.
__Examples:__
`!{ALIAS_NAME} -{ARG_EMPLOYER} \\"The Drunken Yeti\\" -{ARG_CHECK} performance`
`!{ALIAS_NAME} -{ARG_EMPLOYER} \\"Messenger Service\\" -{ARG_CHECK} acrobatics`

If your job calls for a tool check, your check name should be the stat associated with the tool.
Proficiency and expertise bonuses will not be automatically added, in this case;
to add them, provide a `new_bonuses_value`.

__Examples:__
`!{ALIAS_NAME} -{ARG_EMPLOYER} \\"The Drunken Yeti\\" -{ARG_CHECK} charisma -{ARG_BONUS} 2[proficiency]`"

-f "Next Time|Just run `!{ALIAS_NAME}`. 
Don\'t pass an `employer_name` this time, or else your wages and job will get reset.
You can still change `check_name` and modify `bonus_value` with no problems.
If you have advantage on the check, you can specify this by appending `adv` to the command.

__Examples:__
`!{ALIAS_NAME}`
`!{ALIAS_NAME} adv`
`!{ALIAS_NAME} -{ARG_CHECK} athletics adv`"

-f "help|`!{ALIAS_NAME} ?` or `!{ALIAS_NAME} help`
Displays this help message!"
'''

args = &&&
parsed_args = argparse(args)

if args and args[0] in ["?", "help"]:
    return HELP_TEXT

out = [
    f'-title "{name} does part-time work!"',
    f'-thumb {image}'
    f'-color {color}'
]

desc_builder = []
errors = []
job_modifications = []

if exists(CVAR_PTW):
    job_details = load_json(ptw_details)
else:
    job_details = {key: None for key in [
        FIELD_EMPLOYER,
        FIELD_LAST_ATTENDED,
        FIELD_WAGE,
        FIELD_CHECK,
        FIELD_BONUS]}

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
desc_builder.append(f'**Lifestyle:** {last_lifestyle_name.title()}')
lifestyle_details = LIFESTYLES[last_lifestyle_name]

if get_cc(CC_DTDS) == 0:
    errors.append(f'-f "Error: No DTDs|You have no downtime days left!"')

# Determine and report employer
new_employer = parsed_args.last(ARG_EMPLOYER)
if new_employer:
    job_details[FIELD_EMPLOYER] = new_employer
    job_details[FIELD_WAGE] = STARTING_WAGE
    job_details[FIELD_BONUS] = None
    job_details[FIELD_LAST_ATTENDED] = None
    job_modifications.append(f'Employer set to {new_employer}')

employer = job_details.get(FIELD_EMPLOYER)
if employer:
    desc_builder.append(f'**Employer:** {employer.title()}')
else:
    errors.append(f'-f "Error: No Employer|You must set your employer using `-{ARG_EMPLOYER}`.\nExample: `!{ALIAS_NAME} -{ARG_EMPLOYER} \\"The Drunken Yeti\\"`"')

# Check attendance, deliver pay cuts
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

job_details[FIELD_LAST_ATTENDED] = current_time_sec


# Check
new_check = parsed_args.last(ARG_CHECK)

if new_check:
    matches = [x for x in get_raw().skills.keys() if new_check.lower() in x.lower()]
    check = matches[0] if matches else None

    if check:
        job_details[FIELD_CHECK] = check
        job_modifications.append(f'Skill check set to {new_check}')
    else:
        errors.append(f'''\
-f "Error: Invalid Check|`{new_check}` is not a valid value for `-{ARG_CHECK}`.
Try again with the name of a skill or ability.

Examples:
`!{ALIAS_NAME} -{ARG_CHECK} performance`
(sets check to performance; will automatically include proficiency/expertise)

`!{ALIAS_NAME} -{ARG_CHECK} wisdom -{ARG_BONUS} 2`
(Use this if you are working with a tool check. Sets check to Wisdom, \
with a flat additional bonus of 2; you would use this to represent, \
for example, a +2 proficiency bonus.)"\
''')

new_bonuses = parsed_args.get(ARG_BONUS)

if new_bonuses:
    job_details[FIELD_BONUS] = [str(bonus) for bonus in new_bonuses]
    job_modifications += [f'Check bonus added: {bonus}' for bonus in job_details[FIELD_BONUS]]

check_name = job_details.get(FIELD_CHECK)
if check_name and not errors and job_details[FIELD_WAGE] and job_details[FIELD_WAGE] > 0:

    # TODO: turn adv into a setting, so it doesn't need to be passed every time.
    adv_dice = parsed_args.adv()
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

    # TODO: Automated Payment

elif not check_name:
    errors.append(f'''\
-f "Error: No Check|You must set your skill check using `-{ARG_CHECK}`.
Examples:
`!{ALIAS_NAME} -{ARG_CHECK} performance`
(Sets check to performance; will automatically include proficiency/expertise)

`!{ALIAS_NAME} -{ARG_CHECK} wisdom -{ARG_BONUS} 2`
(Use this if you are working with a tool check. Sets check to Wisdom, \
with a flat additional bonus of 2; you would use this to represent, \
for example, a +2 proficiency bonus.)"\
''')

# Check if they've been fired
if job_details[FIELD_WAGE] and job_details[FIELD_WAGE] <= 0:
    desc_builder.clear()
    out.append(f'''\
-f "Fired!|Because your wage has dropped to zero, you have been **fired.**
If you got a new job, you will need to rerun this command \
and specify your new employer with the `-{ARG_EMPLOYER}` argument.

Example:
`!{ALIAS_NAME} -{ARG_EMPLOYER} \\"The Drunken Yeti\\" -{ARG_CHECK} performance`"\
''')

# Combine output
out.append(f'-desc "{NEWLINE_DELIM.join(desc_builder)}"')

if job_modifications:
    out.append(f'-f "Job Modifications|{NEWLINE_DELIM.join(job_modifications)}"')

if errors:
    errors.append('-desc "There were some problems with the command; no changes have been made."')
    return " ".join(errors)
else:
    set_cvar(CVAR_PTW, dump_json(job_details))
    return " ".join(out)
</drac2>
