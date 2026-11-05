a = 9;
b = 19;
if (a + b == 21) {
	print(a);
} else {
	print(b);
} finally {
	print(a + b);
}

while (a < b) {
	print(b - a);
	a = a + 1;
} finally {
	print(a*b);
}
