! rule: S15.2.2.2-007
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
subroutine primary(x)
  implicit none
  integer, intent(out) :: x
  x = 42
  return
entry alternate(x)
  x = 42
end subroutine
subroutine leave_sentinel(x)
  implicit none
  integer, intent(inout) :: x
  x = x
end subroutine
program subprogram_and_entry
  implicit none
  integer :: result
  interface
    subroutine primary(x)
      integer, intent(out) :: x
    end subroutine
    subroutine alternate(x)
      integer, intent(out) :: x
    end subroutine
    subroutine leave_sentinel(x)
      integer, intent(inout) :: x
    end subroutine
  end interface
  result = -6
  call primary(result)
  if (result /= 42) error stop 1
  result = -7
  call alternate(result)
  if (result /= 42) error stop 2
  print '(a)', 'PROCEDURES 15.2.2.2 SUBPROGRAM AND ENTRY OK'
end program
