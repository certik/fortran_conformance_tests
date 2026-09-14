! rule: S6.3.2.3-001
! covers: inline-comment literal-context edit-descriptor-context
! evidence: effect
program comment_contexts
  implicit none
  integer :: value, ios
  character(len=3) :: a, b
  character(len=6) :: record
  value = -1
  a = '?'
  b = '?'
  record = '?'
  ios = -1
  value = 17 ! ; value = 99 & ' " (
  if (value /= 17) error stop 1
  a = 'A!B'
  b = "C!D"
  if (a /= 'A!B') error stop 2
  if (b /= "C!D") error stop 3
  if (iachar(a(2:2)) /= 33) error stop 6
  if (iachar(b(2:2)) /= 33) error stop 7
  write(record, 100, iostat=ios)
  if (ios /= 0) error stop 4
  if (record /= 'E!FG!H') error stop 5
  if (iachar(record(2:2)) /= 33) error stop 8
  if (iachar(record(5:5)) /= 33) error stop 9
100 format('E!F', "G!H") ! ; record = 'wrong'
end program
