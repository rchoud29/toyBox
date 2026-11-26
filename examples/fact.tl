fn factorial(n:u32):u32 {
	df fact:u32 = 1, i:u32;

	for (st i = 1; i <= n; st i++) {
		st fact *= i;
	}

	return fact;
}

fn main():u32 {
	df n:u32 = 5;
	df fact:u32 = factorial(n);
	return fact;
}
