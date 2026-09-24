module expr_c1005_logical_false
  implicit none
  interface operator(.false.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = x
  end function u
end module expr_c1005_logical_false
