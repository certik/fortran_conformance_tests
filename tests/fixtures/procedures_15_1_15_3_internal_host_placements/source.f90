! rule: S15.2.2.2-003
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module internal_host_placements_m
  implicit none
contains
  subroutine module_wrapper(y)
    integer, intent(out) :: y
    y = answer()
  contains
    integer function answer()
      answer = 42
    end function
  end subroutine
end module
subroutine external_wrapper(y)
  implicit none
  integer, intent(out) :: y
  y = answer()
contains
  integer function answer()
    answer = 42
  end function
end subroutine
program internal_host_placements
  use internal_host_placements_m
  implicit none
  integer :: y
  interface
    subroutine external_wrapper(y)
      integer, intent(out) :: y
    end subroutine
  end interface
  y = -1
  call main_wrapper(y)
  if (y /= 42) error stop 1
  call external_wrapper(y)
  if (y /= 42) error stop 2
  call module_wrapper(y)
  if (y /= 42) error stop 3
  print '(a)', 'PROCEDURES 15.2.2.2 INTERNAL HOST PLACEMENTS OK'
contains
  subroutine main_wrapper(y)
    integer, intent(out) :: y
    y = answer()
  end subroutine
  integer function answer()
    answer = 42
  end function
end program
