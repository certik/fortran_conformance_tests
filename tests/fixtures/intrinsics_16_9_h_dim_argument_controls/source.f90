! rule: S16.9.72-001
! covers: DIM-X-integer-or-real
! covers: DIM-Y-same-type-kind-as-X
program i169h_dim_argument_controls
  implicit none
  integer :: checks
  integer :: ix, iy
  real :: rx, ry
  checks = 0
  ix = 7; iy = 2; rx = 4.0; ry = 1.0
  call require('DIM admits integer and real X', dim(ix, iy) == 5 .and. dim(rx, ry) == 3.0, checks)
  call require('DIM requires and uses same type kind pair', kind(dim(rx, ry)) == kind(rx), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIM ARGUMENT CONTROLS OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
end program i169h_dim_argument_controls
