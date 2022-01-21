# Commonsense Validation and Explanation (ComVE) Challenge!

The task is to directly test whether a system can differentiate natural language statements that make sense from those that do not make sense. We designed three subtasks. 

### The first task is to choose from two natural language statements with similar wordings which one makes sense and which one does not make sense; 

### The second task is to find the key reason from three options why a given statement does not make sense;

### The third task asks machine to generate the reasons and we use BLEU to evaluate them.

## Example:
# Task A: Validation
Task: Which statement of the two is against common sense?
Statement1: He put a turkey into the fridge.
Statement2: He put an elephant into the fridge.


# Task B: Explanation (Multi-Choice)
Task: Select the most corresponding reason why this statement is against common sense.
Statement: He put an elephant into the fridge.
A: An elephant is much bigger than a fridge.
B: Elephants are usually white while fridges are usually white.
C: An elephant cannot eat a fridge.


# Task C: Explanation (Generation)
Task: Generate the reason why this statement is against common sense and we will use BELU to evaluate it.
Statement: He put an elephant into the fridge.
Referential Reasons:
1. An elephant is much bigger than a fridge.
2. A fridge is much smaller than an elephant.
3. Most of the fridges aren’t large enough to contain an elephant.
