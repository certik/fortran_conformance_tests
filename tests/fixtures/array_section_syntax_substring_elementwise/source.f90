module array_section_syntax_checks
implicit none
private
integer, save :: checks = 0
public :: check_int_scalar, check_int_rank1, check_char_rank1, finish_checks
contains
subroutine fail(label, why)
  character(*), intent(in) :: label, why
  write(*,'(a,1x,a)') trim(label), trim(why)
  error stop 1
end subroutine fail
subroutine check_int_scalar(label, actual, expected)
  character(*), intent(in) :: label
  integer, intent(in) :: actual(..)
  integer, intent(in) :: expected
  select rank(actual)
  rank(0)
    if (actual /= expected) call fail(label, 'scalar-value')
  rank default
    call fail(label, 'scalar-rank')
  end select
  checks = checks + 1
end subroutine check_int_scalar
subroutine check_int_rank1(label, actual, expected)
  character(*), intent(in) :: label
  integer, intent(in) :: actual(..)
  integer, intent(in) :: expected(:)
  select rank(actual)
  rank(1)
    if (size(actual) /= size(expected)) call fail(label, 'rank1-size')
    if (size(actual) == size(expected)) then
      if (any(actual /= expected)) call fail(label, 'rank1-values')
    end if
  rank default
    call fail(label, 'rank1-rank')
  end select
  checks = checks + 1
end subroutine check_int_rank1
subroutine check_char_rank1(label, actual, expected, expected_len)
  character(*), intent(in) :: label
  character(len=*), intent(in) :: actual(:)
  character(len=*), intent(in) :: expected(:)
  integer, intent(in) :: expected_len
  integer :: i
  if (len(actual) /= expected_len) call fail(label, 'char-length')
  if (len(expected) /= expected_len) call fail(label, 'expected-char-length')
  if (size(actual) /= size(expected)) call fail(label, 'char-size')
  do i = 1, min(size(actual), size(expected))
    if (actual(i) /= expected(i)) call fail(label, 'char-value')
  end do
  checks = checks + 1
end subroutine check_char_rank1
subroutine finish_checks(expected, message)
  integer, intent(in) :: expected
  character(*), intent(in) :: message
  if (checks /= expected) call fail('finish', 'check-count')
  write(*,'(a)') message
end subroutine finish_checks
end module array_section_syntax_checks
program p
use array_section_syntax_checks
implicit none
character(len=5) :: words(-1:1)
words='#####'
words(-1)='abcde'; words(0)='vwxyz'; words(1)='lmnop'
call check_char_rank1('p1 elementwise substrings', words(:)(2:4), &
     [character(len=3)::'bcd','wxy','mno'], 3)
call finish_checks(1, 'ARRAY SECTION SYNTAX SUBSTRING ELEMENTWISE OK')
end program p
