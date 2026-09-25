program procedure_reference_c1524_invalid
  implicit none
  integer :: x
  x = f(*100)
100 continue
contains
  integer function f(n)
    integer, intent(in) :: n
    f = n
  end function
end program procedure_reference_c1524_invalid
