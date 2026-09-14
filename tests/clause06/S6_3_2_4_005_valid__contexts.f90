! rule: S6.3.2.4-005
! covers: paired-markers later-line-control
! evidence: positive-control
program character_markers
  implicit none
  character(len=4) :: a, b, record
  integer :: ios
  a = '?'
  b = '?'
  record = '?'
  ios = -1
  a = 'ab&
! An intervening comment is not part of the literal.
&cd'
  b = "ef&
&gh"
  if (a /= 'abcd') error stop 1
  if (b /= 'efgh') error stop 2
  write(record, 100, iostat=ios)
  if (ios /= 0) error stop 3
  if (record /= 'ijkl') error stop 4
100 format('ij&
&kl')
end program
