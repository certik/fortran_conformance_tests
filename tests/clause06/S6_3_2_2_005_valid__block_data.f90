! rule: S6.3.2.2-005
! covers: block-data end-block-data-no-gaps end-block-data-first-gap end-block-data-second-gap end-block-data-both-gaps
! evidence: positive-control
program block_data_spellings
  implicit none
  integer :: a, b, c, d
  common /blank_one/ a
  common /blank_two/ b
  common /blank_three/ c
  common /blank_four/ d
  if (a /= 1) stop 1
  if (b /= 2) stop 2
  if (c /= 3) stop 3
  if (d /= 4) stop 4
end program

blockdata first
  implicit none
  integer :: a
  common /blank_one/ a
  data a /1/
endblockdata first

block data second
  implicit none
  integer :: b
  common /blank_two/ b
  data b /2/
end blockdata second

block   data third
  implicit none
  integer :: c
  common /blank_three/ c
  data c /3/
endblock data third

block data fourth
  implicit none
  integer :: d
  common /blank_four/ d
  data d /4/
end block data fourth
