! rule: S16.9.72-003
! covers: DIM-positive-difference
! covers: DIM-zero-for-negative-difference
! covers: DIM-negative-operands
program i169h_dim_value_effects
  implicit none
  integer :: checks
  checks = 0
  call require('DIM positive difference exact value', dim(7, 2) == 5, checks)
  call require('DIM negative difference becomes zero with nonzero companion', &
       dim(-3.0, 2.0) == 0.0 .and. dim(2.0, -3.0) == 5.0, checks)
  call require('DIM negative operands subtract before max', dim(-2, -5) == 3, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIM VALUE EFFECTS OK'
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
end program i169h_dim_value_effects
