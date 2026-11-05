a = 10;
b = 5 + 3 * 4 / (2 - 1);
c = 100 - 50 + 25;
print(a);
print(b);
print(c);

is_valid = true;
is_greater = a > 5 && b <= 20;
is_complex = (a == 10 || b != 17) && (c > 0);
print(is_valid);
print(is_greater);
print(is_complex);

{
    block_var = a + b;
    print(block_var);
}

if (a < 5) {
    print(1);
} else if (a == 10) {
    if (b >= 17) {
        print(2);
    }
} else {
    print(3);
} finally {
    print(999);
}

counter = 0;
while (counter < 3) {
    print(counter);
    counter = counter + 1;
} finally {
    print(888);
}

for (i = 0, j = 10; i < 3; { i = i + 1; j = j - 1; }) {
    print(i);
    print(j);
} finally {
    print(777);
}
