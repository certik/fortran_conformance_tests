! rule: S16.9.75-004
! covers: DSHIFTL-shifted-bits-from-operands
! covers: DSHIFTL-ior-shift-equivalence
! covers: DSHIFTL-shift-zero-and-full-width-edges
program i169h_dshiftl_bit_results
  implicit none
  integer :: checks
  integer :: i, j, n, sh, got, expect, edge0, edgew, k
  checks = 0
  n = bit_size(0)
  sh = 4
  i = ior(shiftl(1, 0), shiftl(1, 2))
  j = ior(shiftl(1, n - 1), shiftl(1, n - 3))
  got = dshiftl(i, j, sh)
  expect = ior(shiftl(i, sh), shiftr(j, n - sh))
  edge0 = dshiftl(i, j, 0)
  edgew = dshiftl(i, j, n)
  call require('dshiftl shifted bits come from operands', &
       btest(got, 1) .and. btest(got, 3) .and. btest(got, 4) .and. btest(got, 6), checks)
  call require('dshiftl equals IOR/SHIFT formula on observed bits', &
       all([(btest(got, k) .eqv. btest(expect, k), k = 0, 7)]), checks)
  call require('dshiftl shift zero and full width edges', &
       edge0 /= edgew .and. edge0 == i .and. edgew == j, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTL BIT RESULTS OK'
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
end program i169h_dshiftl_bit_results
