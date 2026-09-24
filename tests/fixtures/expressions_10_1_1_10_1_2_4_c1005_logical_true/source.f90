module expr_c1005_logical_true
  implicit none
  interface operator(.true.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = x
  end function u
end module expr_c1005_logical_true
