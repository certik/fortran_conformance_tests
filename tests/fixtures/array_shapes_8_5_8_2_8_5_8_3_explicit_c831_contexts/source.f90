module explicit_c831_constants
  implicit none
  integer, parameter :: module_n=3
  integer :: module_a(module_n)
end module explicit_c831_constants
program explicit_c831_contexts
  use explicit_c831_constants
  implicit none
  integer, parameter :: main_n=2
  integer :: main_a(main_n)
  integer :: n
  if (size(module_a) /= 3) error stop 'C831 module constant'
  if (size(main_a) /= 2) error stop 'C831 main constant'
  call subprogram_case(4)
  n=5
  block
    integer :: b(n)
    if (size(b) /= 5) error stop 'C831 block nonconstant'
  end block
  write(*,'(a)') 'ARRAY SHAPES C831 OK'
contains
  subroutine subprogram_case(n)
    integer, intent(in) :: n
    integer :: local(n)
    if (size(local) /= 4) error stop 'C831 subprogram nonconstant'
  end subroutine subprogram_case
end program explicit_c831_contexts
