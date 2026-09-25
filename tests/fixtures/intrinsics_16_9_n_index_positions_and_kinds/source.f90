! rule: S16.9.109-002
! covers: INDEX-integer-result
! covers: INDEX-kind-present-result-kind
! covers: INDEX-kind-absent-default-kind
program i169n_index_positions_and_kinds
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer :: pos
  checks = 0
  pos = index('FORTRAN', 'R')
  call require('INDEX result is integer assignment with exact example value', pos == 3, checks)
  call require('INDEX present KIND selects result kind', kind(index('AB', 'B', kind=ik)) == ik, checks)
  call require('INDEX absent KIND is default integer kind', kind(index('AB', 'B')) == kind(0), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INDEX POSITIONS AND KINDS OK'
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
  logical function same_bits(a, b)
    integer, intent(in) :: a, b
    integer :: k
    same_bits = .true.
    do k = 0, bit_size(a) - 1
      if (btest(a, k) .neqv. btest(b, k)) same_bits = .false.
    end do
  end function same_bits
end program i169n_index_positions_and_kinds
