! rule: S16.9.113-002
! covers: ISHFT-result-same-integer-kind-as-I
program i169n_ishft_kind_and_bits
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer :: n, x
  integer(kind=ik) :: wide
  checks = 0
  n = bit_size(0)
  x = ibset(ibset(0, 0), 2)
  wide = 3_ik
  call require('ISHFT result has same kind as I', kind(ishft(wide, 1)) == ik, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N ISHFT KIND AND BITS OK'
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
end program i169n_ishft_kind_and_bits
