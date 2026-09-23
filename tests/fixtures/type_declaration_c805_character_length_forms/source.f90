program main
  implicit none
  integer, parameter :: named_len = 3
  call automatic_len(5)
  block
    character :: literal*3, named*(named_len)
    literal = 'abc'
    named = 'xyz'
    if (len(literal) /= 3) error stop
    if (len(named) /= 3) error stop
    if (literal /= 'abc') error stop
    if (named /= 'xyz') error stop
  end block
  print '(a)', 'type_declaration c805 length forms ok'
contains
  subroutine automatic_len(n)
    integer, intent(in) :: n
    character :: dummy_len*(n)
    dummy_len = 'abcde'
    if (len(dummy_len) /= n) error stop
    if (dummy_len /= 'abcde') error stop
  end subroutine automatic_len
end program main
