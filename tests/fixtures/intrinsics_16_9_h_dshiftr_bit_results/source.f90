! rule: S16.9.76-004
! covers: DSHIFTR-shifted-bits-from-operands
! covers: DSHIFTR-ior-shift-equivalence
! covers: DSHIFTR-shift-zero-and-full-width-edges
program i169h_dshiftr_bit_results
  implicit none
  integer :: checks
  integer :: i, j, n, sh, got, expect, edge0, edgew, k
  checks = 0
  n = bit_size(0)
  sh = 4
  i = ior(shiftl(1, 0), shiftl(1, 2))
  j = ior(shiftl(1, 4), shiftl(1, 6))
  got = dshiftr(i, j, sh)
  expect = ior(shiftl(i, n - sh), shiftr(j, sh))
  edge0 = dshiftr(i, j, 0)
  edgew = dshiftr(i, j, n)
  call require('dshiftr shifted bits come from operands', &
       btest(got, 0) .and. btest(got, 2) .and. btest(got, n - 4) .and. btest(got, n - 2), checks)
  call require('dshiftr equals IOR/SHIFT formula on observed bits', &
       all([(btest(got, k) .eqv. btest(expect, k), k = 0, 7)]), checks)
  call require('dshiftr shift zero and full width edges', &
       edge0 /= edgew .and. edge0 == j .and. edgew == i, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTR BIT RESULTS OK'
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
end program i169h_dshiftr_bit_results
