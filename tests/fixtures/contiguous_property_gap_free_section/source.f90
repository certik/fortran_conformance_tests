program contiguous_property_gap_free_section
  implicit none
  integer :: a(-3:3)
  integer :: i, sh(1)
  do i=-3,3
    a(i)=200+11*i
  end do
  sh=shape(a(-2:2))
  if (is_contiguous(a(-2:2)) .neqv. .true.) error stop 'CP:gap-free-section-contiguous'
  if (lbound(a(-2:2),1) /= 1) error stop 'CP:lb'
  if (ubound(a(-2:2),1) /= 5) error stop 'CP:ub'
  if (sh(1) /= 5) error stop 'CP:shape'
  if (a(-2) /= 178) error stop 'CP:first'
  if (a(2) /= 222) error stop 'CP:last'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK gap_free_section'
end program contiguous_property_gap_free_section
