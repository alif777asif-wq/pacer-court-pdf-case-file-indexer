"""Unit tests for the stamp, court and classification rules. The stamp strings are copied from the pinned real PDFs."""
import pytest

from courtfile.classify import classify
from courtfile.courts import identify_court
from courtfile.stamps import iso_date, parse_stamp

STAMPS = [  # (stamp text as printed on the page, family, case, doc, filed, page, total)
    ("Case 1:21-cv-01061-KLM Document 1 Filed 04/16/21 USDC Colorado Page 1 of 16",
     "district", "1:21-cv-01061-KLM", "1", "2021-04-16", 1, 16),
    ("Case: 1:18-cv-05587 Document #: 1000 Filed: 06/01/21 Page 8 of 18 PageID #:32475",
     "district", "1:18-cv-05587", "1000", "2021-06-01", 8, 18),
    ("Case 18-09232 Doc 49 Filed 04/16/19 Entered 04/16/19 14:07:05 Desc Page 1 of 3",
     "bankruptcy", "18-09232", "49", "2019-04-16", 1, 3),
    ("Case: 20-1507 Document: 00117684624 Page: 1 Date Filed: 12/22/2020 Entry ID: 6390389",
     "appellate", "20-1507", "00117684624", "2020-12-22", 1, None),
    ("Case 17-3510, Document 1-1, 10/31/2017, 2161300, Page1 of 2",
     "appellate", "17-3510", "1-1", "2017-10-31", 1, 2),
    ("Appeal: 17-2218 Doc: 17 Filed: 10/31/2017 Pg: 1 of 1",
     "appellate", "17-2218", "17", "2017-10-31", 1, 1),
    ("Case: 17-2400 Document: 3 Filed: 07/13/2017 Pages: 1",
     "appellate", "17-2400", "3", "2017-07-13", 1, None),
    ("Case: 20-16276, 08/05/2020, ID: 11778722, DktEntry: 19, Page 1 of 15",
     "appellate", "20-16276", "19", "2020-08-05", 1, 15),
    ("Case: 17-2678 Document: 003112692106 Page: 1 Date Filed: 08/03/2017",
     "appellate", "17-2678", "003112692106", "2017-08-03", 1, None),
    ("Case: 17-3994 Document: 1-3 Filed: 09/20/2017 Page: 1",
     "appellate", "17-3994", "1-3", "2017-09-20", 1, None),
    ("Case: 14-1326 Document: 3 Page: 1 Filed: 03/18/2014",
     "appellate", "14-1326", "3", "2014-03-18", 1, None),
    ("Appellate Case: 21-800 Document: 010110462922 Date Filed: 01/11/2021 Page: 1",
     "appellate", "21-800", "010110462922", "2021-01-11", 1, None),
    ("Case 09-00429 Doc 83 Filed 03/09/10 Entered 03/09/10 09:03:58 Document Page 1 of 4",
     "bankruptcy", "09-00429", "83", "2010-03-09", 1, 4),
]


@pytest.mark.parametrize("text,family,case,doc,filed,page,total", STAMPS)
def test_stamp_families(text, family, case, doc, filed, page, total):
    s = parse_stamp(text)
    assert (s.family, s.case_number, s.doc_number, s.filed, s.page, s.total_pages) == (family, case, doc, filed, page, total)


def test_overprinted_stamp_is_not_guessed():
    s = parse_stamp("Case Case 4:08-cv-02214-SBADocument 4:08-cv-02214-SBA Document2627 Filed Filed 01/29/2009 02/03/09 Page 1 of12of 2")
    assert s.case_number == "4:08-cv-02214-SBA"
    assert s.doc_number is None and s.filed is None and s.page is None


def test_caption_fallback():
    assert parse_stamp("IN RE: Bard IVC Filters Products Liability Litigation, No. MDL 15-02641-PHX-DGC").family == "caption"
    assert parse_stamp("no case number anywhere") is None


def test_iso_date_two_digit_years():
    assert iso_date("04/16/21") == "2021-04-16" and iso_date("12/31/99") == "1999-12-31"
    assert iso_date("13/45/2020") is None


@pytest.mark.parametrize("text,level,expected", [
    ("UNITED STATES DISTRICT COURT CENTRAL DISTRICT OF CALIFORNIA", None, "cacd"),
    ("UNITED STATES DISTRICT COURT NORTHERN DISTRICT OF CALIFORNIA", None, "cand"),
    ("IN THE UNITED STATES DISTRICT COURT FOR THE DISTRICT OF ARIZONA", None, "azd"),
    ("UNITED STATES BANKRUPTCY COURT NORTHERN DISTRICT OF ILLINOIS", "bankruptcy", "ilnb"),
    ("UNITED STATES DISTRICT COURT WESTERN DISTRICT OF NEW YORK", None, "nywd"),
    ("UNITED STATES DISTRICT COURT FOR THE DISTRICT OF COLUMBIA", None, "dcd"),
    ("United States Court of Appeals For the First Circuit", "appellate", "ca1"),
    ("UNITED STATES COURT OF APPEALS FOR THE FEDERAL CIRCUIT", None, "cafc"),
    ("Case 1:21-cv-01061-KLM Document 1 Filed 04/16/21 USDC Colorado Page 1 of 16", "district", "cod"),
    ("a page that never names its court", None, None),
])
def test_court_ids(text, level, expected):
    assert identify_court(text, level) == expected


def test_interior_pages_are_excerpts_not_guesses():
    assert classify("ORDER\nanything", stamp_page=8)[0] == "Excerpt"


def test_order_title_wins_over_motion_words():
    page = "Case 8:16-cv-01261-DOC-KES Document 40 Filed 08/05/16 Page 1 of 4\nORDER GRANTING APPLICATION FOR LEAVE\n"
    assert classify(page, 1)[0] == "Order"


def test_unrecognised_page_is_unclassified():
    assert classify("Case 2:15-cv-05642-CAS-JC Document 465 Filed 08/01/19 Page 1 of 1\n", 1)[0] == "Unclassified"
