! rule: S15.2.2.2-002
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
subroutine left_host(y)
  implicit none
  integer, intent(out) :: y
  y = local_answer()
contains
  integer function local_answer()
    local_answer = 41
  end function
end subroutine
subroutine right_host(y)
  implicit none
  integer, intent(out) :: y
  y = local_answer()
contains
  integer function local_answer()
    local_answer = 42
  end function
end subroutine
subroutine host_assoc_wrapper(y)
  implicit none
  integer, intent(out) :: y
  integer :: base
  base = 40
  y = add_two()
contains
  integer function add_two()
    add_two = base + 2
  end function
end subroutine
program internal_procedure_properties
  implicit none
  integer :: y
  interface
    subroutine left_host(y)
      integer, intent(out) :: y
    end subroutine
    subroutine right_host(y)
      integer, intent(out) :: y
    end subroutine
    subroutine host_assoc_wrapper(y)
      integer, intent(out) :: y
    end subroutine
  end interface
  y = -1
  call main_internal(y)
  if (y /= 42) error stop 1
  call left_host(y)
  if (y /= 41) error stop 2
  call right_host(y)
  if (y /= 42) error stop 3
  call host_assoc_wrapper(y)
  if (y /= 42) error stop 4
  print '(a)', 'PROCEDURES 15.2.2.2 INTERNAL PROPERTIES OK'
contains
  subroutine main_internal(y)
    integer, intent(out) :: y
    y = answer()
  end subroutine
  integer function answer()
    answer = 42
  end function
end program
