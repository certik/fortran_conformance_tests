program p
  implicit real (i)
  interface classify
    procedure classify_integer
    procedure classify_real
  end interface
  ivalue = 4
  if (classify(ivalue) /= 2) error stop 1
  print '(a)', 'implicit_statement single letter real generic ok'
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
