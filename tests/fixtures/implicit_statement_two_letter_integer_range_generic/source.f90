program p
  implicit integer (a-c)
  interface classify
    procedure classify_integer
    procedure classify_real
  end interface
  bvalue = 4
  if (classify(bvalue) /= 1) error stop 1
  print '(a)', 'implicit_statement two letter range generic ok'
contains
  integer function classify_integer(x)
    integer, intent(in) :: x
    classify_integer = 1
  end function classify_integer
  integer function classify_real(x)
    real, intent(in) :: x
    classify_real = 2
  end function classify_real
end program p
