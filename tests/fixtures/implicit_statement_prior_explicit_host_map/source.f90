program p
  implicit integer (a)
  interface classify
    procedure classify_integer
    procedure classify_real
  end interface
  call child
contains
  subroutine child
    apple = 7
    if (classify(apple) /= 1) error stop 1
    print '(a)', 'implicit_statement prior explicit host map ok'
  end subroutine child
  integer function classify_integer(x)
    integer, intent(in) :: x
    classify_integer = 1
  end function classify_integer
  integer function classify_real(x)
    real, intent(in) :: x
    classify_real = 2
  end function classify_real
end program p
