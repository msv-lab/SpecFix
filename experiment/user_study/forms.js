function createForm() {
    // Create the form
    const form = FormApp.create('User Study on Ambiguity in Requirements');
    form.setDescription('Please assess requirements according to the definition provided below: \n\nA requirement is considered ambiguous if it allows for multiple reasonable interpretations or contains contradictions, particularly in the context of the intended functionality. While evaluating, consider how the program should behave under edge cases. Please exclude considerations related to invalid input handling or factors unrelated to functionality, like performance.');

    // Read Google Sheet data
    var ss = SpreadsheetApp.getActiveSpreadsheet(); // Get the currently active spreadsheet
    var sheet = ss.getSheetByName("user_study");
    const data = sheet.getDataRange().getValues();
    data.shift(); // Remove the header row

    // Create all pages and questions
    data.forEach((row, i) => {
        const progress = ((i + 1) / data.length) * 100;

        // Add Part1 page (question without examples)
        form.addPageBreakItem().setTitle(`Requirement ${i + 1} (Progress: ${Math.round(progress)}%)`).setHelpText('A requirement is considered ambiguous if it allows for multiple reasonable interpretations or contains contradictions, particularly in the context of the intended functionality. While evaluating, consider how the program should behave under edge cases. Please exclude considerations related to invalid input handling or factors unrelated to functionality, like performance.');
        form.addMultipleChoiceItem()
            .setTitle(`**Please assess the requirement ${i + 1}**`)
            .setHelpText(row[1])  // requirement_without_examples
            .setRequired(true);

        // Add Part2 page (question with examples)
        form.addPageBreakItem().setTitle(`Requirement ${i + 1} - with original examples (Progress: ${Math.round(progress)}%)`).setHelpText('A requirement is considered ambiguous if it allows for multiple reasonable interpretations or contains contradictions, particularly in the context of the intended functionality. While evaluating, consider how the program should behave under edge cases. Please exclude considerations related to invalid input handling or factors unrelated to functionality, like performance.');
        form.addMultipleChoiceItem()
            .setTitle(`**Please assess the requirement ${i + 1} with original examples**`)
            .setHelpText(row[0])  // requirement
            .setRequired(true);
    });

    // Retrieve all pages and questions
    const items = form.getItems();
    const pageBreaks = items.filter(item => item.getType() === FormApp.ItemType.PAGE_BREAK)
        .map(item => item.asPageBreakItem());
    const questions = items.filter(item => item.getType() === FormApp.ItemType.MULTIPLE_CHOICE)
        .map(item => item.asMultipleChoiceItem());

    // Set navigation logic
    data.forEach((_, i) => {
        const caseIndex = i * 2;  // Each case contains 2 questions
        const part1Question = questions[caseIndex];
        const part2Question = questions[caseIndex + 1];

        // Determine the navigation target
        const nextCasePart1 = i < data.length - 1 ? pageBreaks[(i + 1) * 2] : FormApp.PageNavigationType.SUBMIT;
        const part2Page = pageBreaks[caseIndex + 1];

        // Set navigation for Part1 question
        part1Question.setChoices([
            part1Question.createChoice('Ambiguous', part2Page),
            part1Question.createChoice('Unambiguous', nextCasePart1),
        ]);

        // Set navigation for Part2 question
        part2Question.setChoices([
            part2Question.createChoice('Ambiguous', nextCasePart1),
            part2Question.createChoice('Unambiguous', nextCasePart1),
        ]);
    });

    Logger.log('Form created successfully: ' + form.getEditUrl());
}
