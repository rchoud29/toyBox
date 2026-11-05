for (a = 0, b = 10; a <= b; {a = a + 2; b = b + 1;}) {
	print(a);
	print(b);
} finally {
	print(a);
	print(b);
}
