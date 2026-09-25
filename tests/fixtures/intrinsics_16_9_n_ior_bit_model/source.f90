! rule: S16.9.111-002
! covers: IOR-result-kind-from-I-or-J
program i169n_ior_bit_model
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer(kind=ik) :: mixed
  checks = 0
  mixed = ior(z'05', 2_ik)
  call require('IOR result kind comes from integer operand', &
       kind(ior(5_ik, 3_ik)) == ik .and. kind(ior(z'01', 3_ik)) == ik .and. &
       kind(ior(3_ik, z'01')) == ik, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N IOR BIT MODEL OK'
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
end program i169n_ior_bit_model
