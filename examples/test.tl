fn add(a:u32, b:u32):u32 {
    return a + b;
}

fn main():u32 {
    df x:u32 = 5;
    df y:u32 = add(x, 10);

    while (y > 10) {
        st y = y - 1;
    }

    return y;
}
