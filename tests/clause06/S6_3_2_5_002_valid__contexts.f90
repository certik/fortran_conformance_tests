! rule: S6.3.2.5-002
! covers: literal-exclusion edit-descriptor-exclusion comment-exclusion
! evidence: effect
program semicolon_contexts
  implicit none
  integer :: value, ios
  character(len=3) :: a, b, record
  value = -1
  ios = -1
  a = '?'
  b = '?'
  record = '?'
  a = 'a;b'; b = "c;d"
  if (a /= 'a;b') error stop 1
  if (b /= 'c;d') error stop 2
  if (iachar(a(2:2)) /= 59) error stop 6
  if (iachar(b(2:2)) /= 59) error stop 7
  value = 7 ! ; value = 99
  if (value /= 7) error stop 3
  write(record, 100, iostat=ios)
  if (ios /= 0) error stop 4
  if (record /= 'e;f') error stop 5
  if (iachar(record(2:2)) /= 59) error stop 8
100 format('e;f')
end program
