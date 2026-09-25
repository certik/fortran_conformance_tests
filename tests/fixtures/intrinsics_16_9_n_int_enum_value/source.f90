! rule: S16.9.110-004
! covers: INT-enum-corresponding-integer-value
program i169n_int_enum_value
  implicit none
  integer :: checks
  enum, bind(c)
    enumerator :: enum_negative = -2, enum_positive = 4
  end enum
  checks = 0
  call require('INT enum returns corresponding integer value', &
       int(enum_negative) == -2 .and. int(enum_positive) == 4, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INT ENUM VALUE OK'
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
end program i169n_int_enum_value
