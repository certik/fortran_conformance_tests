! rule: S16.9.77-001
! covers: EOSHIFT-ARRAY-array-any-type
! covers: EOSHIFT-SHIFT-integer-scalar-or-conforming-shape
! covers: EOSHIFT-BOUNDARY-same-type-params-scalar-or-conforming-shape
! covers: EOSHIFT-DIM-integer-scalar-valid-range
program i169h_eoshift_argument_controls
  implicit none
  integer :: checks
  integer :: m(2, 3), r(2, 3), rdim(2, 3), sh(2), b(2)
  character(len=2) :: c(3), cr(3)
  checks = 0
  m = reshape([1, 2, 3, 4, 5, 6], [2, 3])
  sh = [-1, 1]; b = [91, 92]
  c = [character(len=2) :: 'ab', 'cd', 'ef']
  r = eoshift(m, sh, b, dim=2)
  rdim = eoshift(m, 1, 99, dim=1)
  cr = eoshift(c, 1, 'zz')
  call require('EOSHIFT ARRAY admits arrays of different intrinsic types', r(1,1) == 91 .and. cr(3) == 'zz', checks)
  call require('EOSHIFT SHIFT scalar or conforming vector is used', r(1,1) == 91 .and. r(2,3) == 92, checks)
  call require('EOSHIFT BOUNDARY same type parameters are used', len(eoshift(c, 1, 'zz')) == 2 .and. cr(3) == 'zz', checks)
  call require('EOSHIFT DIM valid range selects shifted dimension', rdim(2,1) == 99, checks)
  if (checks /= 4) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT ARGUMENT CONTROLS OK'
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
end program i169h_eoshift_argument_controls
