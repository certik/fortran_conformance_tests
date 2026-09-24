! rule: S16.9.77-002
! covers: EOSHIFT-BOUNDARY-absent-table-types-permitted
program i169h_eoshift_absent_boundary_permission
  implicit none
  integer :: checks
  integer :: ia(3), ir(3)
  real :: ra(3), rr(3)
  complex :: za(3), zr(3)
  logical :: la(3), lr(3)
  character(len=3) :: ca(3), cr(3)
  checks = 0
  ia = [4, 5, 6]; ra = [1.0, 2.0, 3.0]; za = [cmplx(1.0,1.0), cmplx(2.0,2.0), cmplx(3.0,3.0)]
  la = [.true., .true., .true.]; ca = [character(len=3) :: 'abc', 'def', 'ghi']
  ir = eoshift(ia, 1); rr = eoshift(ra, 1); zr = eoshift(za, 1); lr = eoshift(la, 1); cr = eoshift(ca, 1)
  call require('EOSHIFT absent BOUNDARY is permitted for Table 16.4 types', &
       ir(3) == 0 .and. rr(3) == 0.0 .and. zr(3) == (0.0, 0.0) .and. &
       .not. lr(3) .and. len(eoshift(ca, 1)) == 3 .and. cr(3) == '   ', checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT ABSENT BOUNDARY PERMISSION OK'
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
end program i169h_eoshift_absent_boundary_permission
