program contiguous_property_full_character_substring
  implicit none
  character(len=4) :: c(2:5)
  integer :: sentinel(-3:3)
  integer :: i, sh(1)
  do i=-3,3
    sentinel(i)=200+11*i
  end do
  c(2)='ABCD'
  c(3)='EFGH'
  c(4)='IJKL'
  c(5)='MNOP'
  sh=shape(c(2:4)(1:4))
  if (is_contiguous(c(2:4)(1:4)) .neqv. .true.) error stop 'CP:full-character-substring-contiguous'
  if (lbound(c(2:4)(1:4),1) /= 1) error stop 'CP:lb'
  if (ubound(c(2:4)(1:4),1) /= 3) error stop 'CP:ub'
  if (sh(1) /= 3) error stop 'CP:shape'
  if (len(c(2:4)(1:4)) /= 4) error stop 'CP:len'
  if (c(3)(1:4) /= 'EFGH') error stop 'CP:char-payload'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK full_character_substring'
end program contiguous_property_full_character_substring
