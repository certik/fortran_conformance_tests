module expr_c1005_intrinsic_not
  implicit none
  interface operator(.not.)
    module procedure u
  end interface
contains
  logical function u(x)
    logical, intent(in) :: x
    u = .not. x
  end function u
end module expr_c1005_intrinsic_not
