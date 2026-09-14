! rule: S6.3.2.4-004
! covers: split-name split-keyword split-integer split-operator
! evidence: positive-control
program split_tokens
  implicit none
  inte&
&ger :: value
  integer :: answer
  value = -1
  answer = -1
  val&
! The next noncomment line finishes the name.
&ue = 1&
&7
  answer = 2 *&
&* 3
  if (value /= 17) error stop 1
  if (answer /= 8) error stop 2
end program
