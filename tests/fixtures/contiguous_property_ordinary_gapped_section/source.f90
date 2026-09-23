program contiguous_property_ordinary_gapped_section
  implicit none
  integer :: a(-3:3)
  integer :: i, sh(1), gapsh(1)
  do i=-3,3
    a(i)=200+11*i
  end do
  sh=shape(a(-2:2))
  gapsh=shape(a(-3:3:2))
  if (is_contiguous(a(-2:2)) .neqv. .true.) error stop 'CP:positive-control-contiguous'
  if (is_contiguous(a(-3:3:2)) .neqv. .false.) error stop 'CP:gapped-section-not-contiguous'
  if (sh(1) /= 5) error stop 'CP:positive-shape'
  if (lbound(a(-3:3:2),1) /= 1) error stop 'CP:gap-lb'
  if (ubound(a(-3:3:2),1) /= 4) error stop 'CP:gap-ub'
  if (gapsh(1) /= 4) error stop 'CP:gap-shape'
  if (a(-3) /= 167) error stop 'CP:gap-first'
  if (a(3) /= 233) error stop 'CP:gap-last'
  write(*,'(a)') 'CONTIGUOUS PROPERTY OK ordinary_gapped_section'
end program contiguous_property_ordinary_gapped_section
